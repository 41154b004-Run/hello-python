import random
from typing import Tuple, List, Optional

# 使用者風格偏好 (記憶體儲存，亦可擴充至資料庫)
user_styles = {}

# 官方免費用貼圖庫 (Package ID, Sticker ID)
STICKERS = {
    "thumbs_up": ("446", "1988"),      # 熊大比讚
    "wave": ("11537", "52002734"),      # 揮手問好
    "ok": ("11537", "52002735"),        # OK 手勢
    "thank_you": ("11537", "52002736"), # 鞠躬感謝
    "laugh": ("11537", "52002738"),     # 哈哈大笑
    "cheer": ("11537", "52002739"),     # 加油奮鬥
    "cry": ("11537", "52002741"),       # 抱抱安慰
    "love": ("789", "10855"),           # 愛心熊大
    "sleep": ("789", "10884"),          # 晚安睡覺
    "shock": ("11537", "52002744"),     # 震驚
    "sparkle": ("11537", "52002742"),   # 閃閃發光
    "think": ("11537", "52002743"),     # 思考中
    "sweat": ("11537", "52002745"),     # 冷汗
    "wow": ("446", "1989"),             # 哇
    "angry": ("446", "2001"),           # 生氣
    "heart": ("446", "2006"),           # 比心
}

# 所有支援風格列表
STYLE_NAMES = {
    "normal":   "親切夥伴風 😊",
    "tsundere": "傲嬌風 😤",
    "formal":   "專業秘書風 👔",
    "funny":    "幽默搞笑風 🤪",
    "kawaii":   "超萌可愛風 🌸",
    "cool":     "酷炫帥氣風 😎",
}


# 冷笑話庫
JOKES = [
    "有一天，綠豆跳樓變成了什麼？……紅豆，因為流血了！😆",
    "什麼動物最容易摔倒？……狐狸，因為牠狡猾（腳滑）！🦊",
    "有一天皮卡丘走路，走著走著就變成了……皮卡乒乓球！🏓",
    "小明吃了牛肉麵，為什麼還是覺得很餓？……因為那是牛肉「麵」，不是牛肉「飯」！🍜",
    "為什麼企鵝的肚子是白色的？……因為手太短，洗澡只能洗到肚子！🐧",
    "一隻鴨子走在路上，突然打翻了可樂，變成了什麼？……可樂鴨（烤肉呀）！🦆"
]

# 美食庫
FOOD_LIST = [
    "熱騰騰的麻辣火鍋 🍲",
    "日式豚骨拉麵 🍜",
    "酥脆香濃的台式雞排與鹽酥雞 🍗",
    "經典排骨便當加滷蛋 🍱",
    "義式白醬培根義大利麵 🍝",
    "炙燒鮭魚握壽司 🍣",
    "現烤窯烤披薩 🍕",
    "牛肉麵配一盤現切小菜 🥩",
    "香噴噴的鐵板燒料理 🍳",
    "清爽的健康舒肥雞胸溫沙拉 🥗"
]

# 運勢資料庫
FORTUNES = [
    {"level": "🌟 大吉！", "desc": "今天氣場全開，做什麼事情都順風順水！", "color": "香檳金", "num": 7},
    {"level": "✨ 中吉！", "desc": "心情愉悅的一天，適合學習新知識或聯絡老朋友。", "color": "天空藍", "num": 3},
    {"level": "🌿 小吉！", "desc": "平淡即是福，保持步調，會有意想不到的小幸運發生。", "color": "薄荷綠", "num": 8},
    {"level": "💖 桃花吉！", "desc": "今天魅力值破表，對身邊的人笑一個吧！", "color": "櫻花粉", "num": 5},
    {"level": "🍀 吉！", "desc": "努力會被看見，維持正能量，好運隨之而來！", "color": "陽光橙", "num": 9},
]

def get_user_style(user_id: str) -> str:
    """取得使用者目前的對話風格"""
    return user_styles.get(user_id, "normal")

def set_user_style(user_id: str, style: str) -> str:
    """設定使用者對話風格"""
    if style in STYLE_NAMES:
        user_styles[user_id] = style
        return f"✅ 已成功切換為【{STYLE_NAMES[style]}】！快跟我說句話試試看吧～"
    options = "\n".join([f"• /style {k} : {v}" for k, v in STYLE_NAMES.items()])
    return f"❌ 未知風格，請選擇以下其中一個：\n{options}"

def build_sticker_response() -> Tuple[str, Tuple[str, str]]:
    """收到貼圖時的回應文字與對應貼圖（更豐富的回應池）"""
    responses = [
        ("好可愛的貼圖！我也回你一個～ ✨", STICKERS["love"]),
        ("收到你的貼圖囉！擊掌高飛 ✋", STICKERS["cheer"]),
        ("哈哈這貼圖太生動了吧！讚啦 👍", STICKERS["thumbs_up"]),
        ("你傳貼圖我秒回，這就是默契！😎", STICKERS["laugh"]),
        ("叮咚！機器人接收到元氣貼圖能量 ⚡", STICKERS["wave"]),
        ("哇！這個貼圖選得太有品味了！✨", STICKERS["sparkle"]),
        ("嘿嘿～你傳貼圖給我，我當然要回你更可愛的！🌸", STICKERS["heart"]),
        ("你的貼圖讓我的電路都暖了起來 💕", STICKERS["love"]),
        ("收到！這個表情好符合我現在的心情喔 🌟", STICKERS["wow"]),
    ]
    return random.choice(responses)


def process_smart_chat(user_text: str, user_id: str) -> Tuple[str, Optional[Tuple[str, str]]]:
    """
    依據關鍵字與目前風格生成富有情緒與表現力的回覆與貼圖
    回傳 (文字內容, 貼圖資訊元組 或 None)
    """
    style = get_user_style(user_id)
    text_clean = user_text.strip().lower()

    # 1. 笑話小工具
    if any(k in text_clean for k in ["講笑話", "說笑話", "/joke", "笑話"]):
        joke = random.choice(JOKES)
        return (f"🎭 來個冷笑話放鬆一下：\n\n{joke}", STICKERS["laugh"])

    # 2. 運勢占卜
    if any(k in text_clean for k in ["運勢", "今日運勢", "抽籤", "/fortune", "占卜"]):
        fortune = random.choice(FORTUNES)
        reply = (
            f"🔮 【今日運勢占卜】\n"
            f"--------------------\n"
            f"命定運勢：{fortune['level']}\n"
            f"運勢解析：{fortune['desc']}\n"
            f"幸運色彩：{fortune['color']}\n"
            f"幸運數字：{fortune['num']}"
        )
        return (reply, STICKERS["cheer"])

    # 3. 美食推薦
    if any(k in text_clean for k in ["吃什麼", "吃啥", "/food", "午餐吃什麼", "晚餐吃什麼", "美食推薦"]):
        food = random.choice(FOOD_LIST)
        reply = f"🍽️ 靈感推薦：今天就決定去吃【{food}】吧！\n吃飽才有力氣繼續加油～"
        return (reply, STICKERS["thumbs_up"])

    # 4. 問候類
    if any(k in text_clean for k in ["早安", "早啊", "早上好"]):
        if style == "tsundere":
            return ("哼，早、早安！可別以為我起得早是在等你的訊息喔！😤", STICKERS["shock"])
        elif style == "formal":
            return ("早安！祝您今天晨光燦爛，工作與學習一切順遂。", STICKERS["thumbs_up"])
        elif style == "funny":
            return ("早安！起床第一件事是伸懶腰，第二件事是跟我打招呼～好習慣！🌅", STICKERS["wave"])
        else:
            return ("早安早安！新的一天也要元氣滿滿喔 ☀️", STICKERS["wave"])

    if any(k in text_clean for k in ["午安", "中午好"]):
        return ("午安！中餐記得吃飽飽，稍微休息小憩一下更有精神喔 🍱", STICKERS["thumbs_up"])

    if any(k in text_clean for k in ["晚安", "去睡了", "睡覺"]):
        if style == "tsundere":
            return ("這麼早就要睡啦？……哼，那、那祝你好夢就是了，晚安！💤", STICKERS["sleep"])
        elif style == "formal":
            return ("晚安。請好好放鬆休息，期待明日繼續為您提供服務。", STICKERS["sleep"])
        else:
            return ("辛苦了一整天，晚安囉！蓋好被子做個好夢 🌙", STICKERS["sleep"])

    if any(k in text_clean for k in ["你好", "嗨", "哈囉", "hello", "hi"]):
        if style == "tsundere":
            return ("看、看到你了啦！有什麼事快說，我可沒閒著呢～ 😏", STICKERS["wave"])
        elif style == "formal":
            return ("您好！很高興為您服務。請隨時告知您的需求。", STICKERS["ok"])
        else:
            return ("嗨嗨！很高興見到你～有什麼我可以幫忙的嗎？✨", STICKERS["wave"])

    # 5. 感謝與誇獎
    if any(k in text_clean for k in ["謝謝", "感謝", "感恩", "thx", "thank"]):
        if style == "tsundere":
            return ("哼……隨便幫個忙而已，才不用特地跟我道謝呢！(臉紅) ⁄(⁄ ⁄•⁄-⁄•⁄ ⁄)⁄", STICKERS["love"])
        elif style == "formal":
            return ("不客氣，能為您提供協助是我的榮幸。", STICKERS["thank_you"])
        else:
            return ("不客氣啦！能幫上你的忙我也超開心的～ 😊", STICKERS["thank_you"])

    if any(k in text_clean for k in ["好棒", "厲害", "讚", "超強", "聰明", "你好厲害"]):
        if style == "kawaii":
            return ("哇哇哇！你誇我我好害羞喔～謝謝你啦！(≧▽≦) 🌸", STICKERS["love"])
        return ("耶！被誇獎了～（轉圈灑花）🎉 我會繼續努力進步的！", STICKERS["love"])

    # 6. 安慰與傾聽
    if any(k in text_clean for k in ["好累", "好辛苦", "累死", "辛苦了"]):
        if style == "kawaii":
            return ("哎呀～辛苦你了！給你一個大大的元氣抱抱！(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", STICKERS["cheer"])
        elif style == "cool":
            return ("撐住，你比你想的還要強。休息是為了走更長遠的路。", STICKERS["cheer"])
        return ("今天真的辛苦你了！好好喝杯熱茶，給自己一個大大的擁抱，你已經做得很棒了 🍵", STICKERS["cheer"])

    if any(k in text_clean for k in ["心情不好", "難過", "傷心", "想哭"]):
        if style == "kawaii":
            return ("不要難過嘛 >(ᴗ_ ᴗ)< 我在這裡陪你喔！一起加油好不好？💕", STICKERS["cry"])
        elif style == "cool":
            return ("負面情緒是暫時的。允許自己感受，然後繼續前行。我在這。", STICKERS["cry"])
        return ("拍拍你……不論遇到什麼煩惱，我都隨時在這裡陪你說說話喔 ❤️", STICKERS["cry"])

    if any(k in text_clean for k in ["笑死", "哈哈", "xd", "lol", "太好笑了", "哈哈哈"]):
        return ("哈哈哈哈哈～有這麼好笑嗎！我也跟著笑出來了 🤣", STICKERS["laugh"])

    # 7. 預設多樣化對話風格 (Default Chit-Chat — Gemini 會處理真正的問答)
    if style == "tsundere":
        replies = [
            f"你說「{user_text}」是什麼意思啦？我才沒有特別在意你說的話呢！😤",
            f"「{user_text}」……哼，勉強聽懂了啦！還有其他話想對我說嗎？",
            f"真是的，突然說「{user_text}」，我可不是隨時都有空聽你碎碎念的喔！（但…其實我有在聽）",
        ]
        return (random.choice(replies), STICKERS["shock"])
    elif style == "formal":
        replies = [
            f"已收到您的訊息：『{user_text}』。系統運作一切正常，隨時等候指令。",
            f"關於您所提及的『{user_text}』，已納入交談紀錄。如需協助請輸入 /help。",
            f"感謝您的交流：『{user_text}』。祝您順心如意。",
        ]
        return (random.choice(replies), None)
    elif style == "funny":
        replies = [
            f"「{user_text}」？！天啊，這句話太有哲理了，我必須拿螢光筆畫三條重點線！🖍️",
            f"你剛才說了「{user_text}」對吧？本機器人的超級運算腦袋正在瘋狂旋轉中～ 🌀",
            f"收到信號：「{user_text}」！無聊的話跟我說「講笑話」，包準你笑到合不攏嘴！😂",
        ]
        return (random.choice(replies), STICKERS["laugh"])
    elif style == "kawaii":
        replies = [
            f"嗚哇～「{user_text}」！好有趣喔 (｡♥‿♥｡) 告訴我更多更多！🌸",
            f"你說「{user_text}」，我聽到了喔！超級認真地在聽你說話呢 ≧(´▽`)≦",
            f"「{user_text}」！嘿嘿，你說的話讓我心情都變好了！(≧◡≦) 💕",
        ]
        return (random.choice(replies), STICKERS["heart"])
    elif style == "cool":
        replies = [
            f"Got it. 「{user_text}」— 簡短有力。有什麼需要我做的嗎？",
            f"「{user_text}」。收到。保持這種效率。",
            f"了解，「{user_text}」。行動比言語更有力量。",
        ]
        return (random.choice(replies), None)
    else:  # normal — 回傳 None 讓 handlers 呼叫 Gemini
        return ("", None)  # 空字串代表「交給 Gemini 回答」

