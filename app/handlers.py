from datetime import datetime
import json
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent
)

def register_handlers(handler, configuration):
    """註冊 LINE Webhook 事件處理器"""

    @handler.add(FollowEvent)
    def handle_follow(event: FollowEvent):
        """當使用者加入機器人好友時觸發"""
        welcome_text = (
            "🎉 歡迎加入！我是您的 Python LINE 助理。\n\n"
            "您可以隨時輸入文字與我對話，或是輸入以下指令體驗功能：\n"
            "👉 「/help」- 查看指令說明\n"
            "👉 「/date」- 查詢今天日期與時間\n"
            "👉 「/countdown」- 啟動倒數計時\n"
            "👉 「/card」- 查看範例 Flex 卡片"
        )
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=welcome_text)]
                )
            )

    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text_message(event: MessageEvent):
        """處理文字訊息"""
        user_text = event.message.text.strip()
        user_lower = user_text.lower()

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            # 1. 幫助與指令列表
            if user_lower in ["/help", "help", "幫助", "指令", "選單"]:
                reply_content = (
                    "🤖 【指令選單】\n"
                    "----------------------\n"
                    "• /date 或 日期 : 查看當前系統日期與時間\n"
                    "• /countdown [秒數] : 倒數計時 (預設 3 秒)\n"
                    "• /card 或 卡片 : 展示精緻 Flex 卡片\n"
                    "• 輸入其他任何文字 : 回音測試 (Echo)"
                )
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_content)]
                    )
                )
                return

            # 2. 取得動態日期與時間
            if user_lower in ["/date", "date", "日期", "今天"]:
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

            # 3. 倒數計時功能 (傳承 hello.py 的 countdown 概念)
            if user_lower.startswith("/countdown") or user_lower.startswith("倒數"):
                parts = user_text.split()
                seconds = 3
                if len(parts) > 1 and parts[1].isdigit():
                    seconds = min(int(parts[1]), 10)  # 最大限制 10 秒
                
                countdown_steps = [f"{i}..." for i in range(seconds, 0, -1)]
                countdown_str = "\n".join(countdown_steps)
                reply_content = f"⏱️ 倒數計時 ({seconds} 秒)：\n{countdown_str}\n🎉 倒數結束！"
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_content)]
                    )
                )
                return

            # 4. 展示 Flex Message 卡片
            if user_lower in ["/card", "card", "卡片"]:
                bubble_dict = {
                    "type": "bubble",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "Python LINE Bot", "weight": "bold", "color": "#1DB446", "size": "sm"},
                            {"type": "text", "text": "系統功能卡片", "weight": "bold", "size": "xl", "margin": "md"}
                        ]
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "此機器人採用 FastAPI + line-bot-sdk v3 架構開發，具備高擴充性。", "wrap": True, "size": "sm", "color": "#666666"},
                            {"type": "separator", "margin": "lg"},
                            {
                                "type": "box",
                                "layout": "vertical",
                                "margin": "lg",
                                "spacing": "sm",
                                "contents": [
                                    {"type": "text", "text": "✔ 支援簽章驗證 (X-Line-Signature)", "size": "xs", "color": "#333333"},
                                    {"type": "text", "text": "✔ 支援 Flex 豐富格式訊息", "size": "xs", "color": "#333333"},
                                    {"type": "text", "text": "✔ 支援自訂指令分發處理", "size": "xs", "color": "#333333"}
                                ]
                            }
                        ]
                    }
                }
                flex_container = FlexContainer.from_json(json.dumps(bubble_dict))
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[FlexMessage(alt_text="Python LINE Bot 功能展示", contents=flex_container)]
                    )
                )
                return

            # 5. 預設回音 (Echo)
            echo_reply = f"你說了：「{user_text}」\n\n💡 提示：輸入「/help」可查看指令選單"
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=echo_reply)]
                )
            )
