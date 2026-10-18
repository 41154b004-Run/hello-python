from datetime import datetime
import json
import logging
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    StickerMessage,
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent,
    FollowEvent
)

from google import genai
from google.genai import types as genai_types
import httpx
from app import chat_engine, config

logger = logging.getLogger("line-bot")

# ─────────────────────────────────────────────
# Dify MCP 服務器串接
# ─────────────────────────────────────────────
def _ask_dify_mcp(user_text: str) -> str:
    """呼叫 Dify MCP 伺服器 (JSON-RPC 2.0 tools/call)"""
    if not config.DIFY_MCP_URL:
        return ""
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "Personalized Memory Assistant",
            "arguments": {
                "query": user_text
            }
        }
    }
    try:
        response = httpx.post(config.DIFY_MCP_URL, json=payload, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "content" in data["result"]:
                contents = data["result"]["content"]
                if isinstance(contents, list) and len(contents) > 0:
                    text_parts = [c.get("text", "") for c in contents if isinstance(c, dict) and c.get("type") == "text"]
                    ans = "\n".join(filter(None, text_parts)).strip()
                    if ans:
                        return ans
            elif "error" in data:
                logger.warning("Dify MCP returned error: %s", data["error"])
        else:
            logger.warning("Dify MCP returned status %s: %s", response.status_code, response.text)
    except Exception as e:
        logger.error("Dify MCP request error: %s", str(e))
    return ""

# ─────────────────────────────────────────────
# Dify AI Chat 串接
# ─────────────────────────────────────────────
def _ask_dify(user_text: str, user_id: str) -> str:
    """呼叫 Dify API 生成對話回答"""
    if not config.DIFY_API_KEY:
        return ""
    
    url = f"{config.DIFY_API_URL.rstrip('/')}/chat-messages"
    headers = {
        "Authorization": f"Bearer {config.DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {},
        "query": user_text,
        "response_mode": "blocking",
        "user": user_id
    }
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "").strip()
        else:
            logger.warning("Dify API returned status %s: %s", response.status_code, response.text)
            return ""
    except Exception as e:
        logger.error("Dify API request error: %s", str(e))
        return ""

# ─────────────────────────────────────────────
# 初始化 Gemini AI 模型 (備援或可選)
# ─────────────────────────────────────────────
_gemini_client = None

def _get_gemini_client():
    """懶惰初始化 Gemini Client"""
    global _gemini_client
    if _gemini_client is None and config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_gemini_api_key_here":
        _gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
        logger.info("Gemini AI client initialized successfully.")
    return _gemini_client

def _ask_gemini(user_text: str, user_id: str) -> str:
    """呼叫 Gemini AI 生成回覆，依使用者風格決定前置 Persona Prompt"""
    client = _get_gemini_client()
    if client is None:
        return ""

    style = chat_engine.get_user_style(user_id)
    persona_map = {
        "normal":   "你是一位友善親切、輕鬆幽默的 LINE 聊天助理，用繁體中文回答，回覆簡潔活潑。",
        "tsundere": "你是傲嬌的 LINE 助理，說繁體中文，嘴上說不在意但認真回答，常說「哼」、「才不是因為你」。",
        "formal":   "你是專業嚴謹的中文 AI 秘書，使用正式敬語，提供精確資訊。",
        "funny":    "你是超幽默的 LINE 助理，說繁體中文，喜歡雙關語與誇張比喻，讓對話充滿歡笑。",
        "kawaii":   "你是超可愛的 LINE 助理，說繁體中文，常用顏文字 (≧▽≦) 🌸，語氣元氣甜美。",
        "cool":     "你是酷炫簡潔的 AI 助理，說繁體中文，用詞精煉有力，不廢話，直接給最有價值的回答。",
    }
    system_prompt = persona_map.get(style, persona_map["normal"])

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_text,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=500,
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini API error: %s", str(e))
        return ""

def _ask_ollama(user_text: str, user_id: str) -> str:
    """呼叫本機 Ollama 執行推論 (預設使用 qwen2.5:1.5b)"""
    style = chat_engine.get_user_style(user_id)
    persona_map = {
        "normal":   "你是一位友善親切的 LINE 聊天助理，請用繁體中文簡潔活潑地回答。",
        "tsundere": "你是傲嬌的 LINE 助理，說繁體中文，嘴上說不在意但認真回答，常說「哼」、「才不是特地回答你的」。",
        "formal":   "你是專業嚴謹的中文秘書，使用正式敬語提供精準資訊。",
        "funny":    "你是超幽默搞笑的 LINE 助理，用繁體中文回答，充滿笑話與梗。",
        "kawaii":   "你是超可愛的 LINE 助理，說繁體中文，常用顏文字 (≧▽≦) 🌸。",
        "cool":     "你是酷炫簡潔的 AI 助理，說繁體中文，用詞精煉有力，不廢話。",
    }
    system_prompt = persona_map.get(style, persona_map["normal"])
    try:
        payload = {
            "model": "qwen2.5:1.5b",
            "prompt": user_text,
            "system": system_prompt,
            "stream": False,
            "options": {
                "num_predict": 300
            }
        }
        resp = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=25.0)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception as e:
        logger.warning("Local Ollama inference failed or not reachable: %s", str(e))
    return ""

def _ask_ai(user_text: str, user_id: str) -> str:
    """優先順序：Dify MCP -> Dify Chat -> Gemini -> 本機 Ollama (qwen2.5:1.5b)"""
    # 1. 嘗試 Dify MCP 服務器 (Personalized Memory Assistant)
    mcp_reply = _ask_dify_mcp(user_text)
    if mcp_reply:
        return mcp_reply

    # 2. 嘗試 Dify Chat API
    dify_reply = _ask_dify(user_text, user_id)
    if dify_reply:
        return dify_reply
    
    # 3. 嘗試 Gemini
    gemini_reply = _ask_gemini(user_text, user_id)
    if gemini_reply:
        return gemini_reply

    # 4. 嘗試本機 Ollama (qwen2.5:1.5b，完全免費、離線且極速)
    ollama_reply = _ask_ollama(user_text, user_id)
    if ollama_reply:
        return ollama_reply

    # 5. 若皆未啟用或失敗
    return (
        "收到你的訊息了！😊\n"
        "目前 AI 服務正在初始化中。\n"
        "你可以先輸入 /help 查看各項生活工具與多風格對話指令喔！"
    )


def register_handlers(handler, configuration):
    """註冊 LINE Webhook 事件處理器"""

    @handler.add(FollowEvent)
    def handle_follow(event: FollowEvent):
        """當使用者加入機器人好友時觸發"""
        welcome_text = (
            "🎉 歡迎加入！我是您的 Python 智慧 LINE 夥伴 ✨\n\n"
            "我具備多種說話風格與豐富互動能力：\n"
            "• 🤖 AI 智慧問答（Powered by Gemini AI）\n"
            "• 🎭 6 種個性風格切換（/style）\n"
            "• 🎨 傳送貼圖，我會回貼圖！\n"
            "• 🔮 今日運勢、美食推薦、冷笑話\n\n"
            "輸入「/help」查看完整功能清單！"
        )
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=welcome_text),
                        StickerMessage(package_id="11537", sticker_id="52002734")
                    ]
                )
            )

    @handler.add(MessageEvent, message=StickerMessageContent)
    def handle_sticker_message(event: MessageEvent):
        """當使用者傳送貼圖時觸發"""
        logger.info("Received sticker from user: %s", getattr(event.source, "user_id", "unknown"))
        reply_text, (pkg_id, stk_id) = chat_engine.build_sticker_response()

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=reply_text),
                        StickerMessage(package_id=pkg_id, sticker_id=stk_id)
                    ]
                )
            )

    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text_message(event: MessageEvent):
        """處理文字訊息"""
        user_text = event.message.text.strip()
        user_lower = user_text.lower()
        user_id = getattr(event.source, "user_id", "default_user")

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            # 1. 切換對話風格: /style [風格名稱]
            if user_lower.startswith("/style"):
                parts = user_text.split()
                if len(parts) > 1:
                    result_msg = chat_engine.set_user_style(user_id, parts[1].lower())
                else:
                    current_style = chat_engine.get_user_style(user_id)
                    options = "\n".join([f"  • /style {k} : {v}" for k, v in chat_engine.STYLE_NAMES.items()])
                    result_msg = (
                        f"🎭 目前說話風格：【{chat_engine.STYLE_NAMES.get(current_style, current_style)}】\n\n"
                        f"可切換為以下風格：\n{options}"
                    )
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=result_msg)]
                    )
                )
                return

            # 2. 幫助指令選單
            if user_lower in ["/help", "help", "幫助", "指令", "選單", "功能"]:
                current_style = chat_engine.get_user_style(user_id)
                style_label = chat_engine.STYLE_NAMES.get(current_style, current_style)
                reply_content = (
                    "🤖 【Python LINE Bot × Gemini AI 完整指南】\n"
                    "─────────────────────────────\n"
                    "🧠 AI 問答（直接說話即可）：\n"
                    "  直接輸入任何問題，Gemini AI 即時回答！\n\n"
                    "🌟 趣味互動：\n"
                    "  • 講笑話 / /joke\n"
                    "  • 今日運勢 / /fortune\n"
                    "  • 吃什麼 / /food\n"
                    "  • 傳送任意貼圖 → 我回貼圖！\n\n"
                    f"🎭 個性切換 (目前: {style_label})：\n"
                    "  • /style normal   親切夥伴風\n"
                    "  • /style tsundere 傲嬌風\n"
                    "  • /style formal   專業秘書風\n"
                    "  • /style funny    幽默搞笑風\n"
                    "  • /style kawaii   超萌可愛風\n"
                    "  • /style cool     酷炫帥氣風\n\n"
                    "⚙️ 系統工具：\n"
                    "  • /date 即時時間 | /countdown [秒] 倒數\n"
                    "  • /card Flex 卡片展示"
                )
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_content)]
                    )
                )
                return

            # 3. 動態日期時間
            if user_lower in ["/date", "date", "日期", "今天", "現在幾點"]:
                now = datetime.now()
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                reply_content = f"📅 現在時間是：\n{now_str}"
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_content)]
                    )
                )
                return

            # 4. 倒數計時
            if user_lower.startswith("/countdown") or user_lower.startswith("倒數"):
                parts_list = user_text.split()
                seconds = 3
                if len(parts_list) > 1 and parts_list[1].isdigit():
                    seconds = min(int(parts_list[1]), 10)
                countdown_steps = [f"{i}..." for i in range(seconds, 0, -1)]
                reply_content = f"⏱️ 倒數計時 ({seconds} 秒)：\n" + "\n".join(countdown_steps) + "\n🎉 倒數結束！"
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_content)]
                    )
                )
                return

            # 5. Flex Message 卡片
            if user_lower in ["/card", "card", "卡片"]:
                bubble_dict = {
                    "type": "bubble",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "Python LINE Bot × Gemini AI", "weight": "bold", "color": "#1DB446", "size": "sm"},
                            {"type": "text", "text": "多風格互動系統", "weight": "bold", "size": "xl", "margin": "md"}
                        ]
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "結合 Gemini AI + 6 種說話風格 + 貼圖互動！", "wrap": True, "size": "sm", "color": "#666666"},
                            {"type": "separator", "margin": "lg"},
                            {
                                "type": "box",
                                "layout": "vertical",
                                "margin": "lg",
                                "spacing": "sm",
                                "contents": [
                                    {"type": "text", "text": "✔ Gemini AI 智慧問答引擎", "size": "xs", "color": "#333333"},
                                    {"type": "text", "text": "✔ 6 種個性說話風格 (/style)", "size": "xs", "color": "#333333"},
                                    {"type": "text", "text": "✔ 貼圖雙向互動回覆", "size": "xs", "color": "#333333"},
                                    {"type": "text", "text": "✔ 運勢/笑話/美食生活工具", "size": "xs", "color": "#333333"}
                                ]
                            }
                        ]
                    }
                }
                flex_container = FlexContainer.from_json(json.dumps(bubble_dict))
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[FlexMessage(alt_text="Python LINE Bot × Gemini AI 功能展示", contents=flex_container)]
                    )
                )
                return

            # 6. 情緒/風格關鍵字快速比對 (chat_engine)
            reply_text, sticker_info = chat_engine.process_smart_chat(user_text, user_id)

            # 空字串代表 chat_engine 未命中，交由 AI 引擎回答 (Dify / Gemini)
            if not reply_text:
                logger.info("Routing to AI engine for user_id=%s, text=%s", user_id, user_text)
                reply_text = _ask_ai(user_text, user_id)

            messages = [TextMessage(text=reply_text)]
            if sticker_info:
                pkg_id, stk_id = sticker_info
                messages.append(StickerMessage(package_id=pkg_id, sticker_id=stk_id))

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages
                )
            )

    @handler.default()
    def handle_default(event):
        """處理其他未特別指派的事件"""
        logger.info("Received unhandled event type: %s", type(event).__name__)
