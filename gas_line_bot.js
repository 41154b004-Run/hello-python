/**
 * Google Apps Script (GAS) LINE Bot x Gemini AI 整合腳本
 *
 * 【功能說明】
 * 1. 接收 LINE Webhook 訊息
 * 2. 呼叫 Google Gemini 1.5 Flash / 2.0 Flash API 進行高品質繁體中文回答
 * 3. 自動處理對話風格、貼圖回應與錯誤備援
 * 4. 可直接部署為獨立雲端 Webhook，或作為現有 Python 服務的雲端 AI 轉發節點
 *
 * 【部署步驟】
 * 1. 前往 Google Apps Script (https://script.google.com/) 建立新專案
 * 2. 將此檔案代碼完整貼入 Code.gs
 * 3. 點選專案設定 (齒輪圖示) ->「指令碼屬性 (Script Properties)」，新增：
 *    - LINE_ACCESS_TOKEN : 您的 LINE Channel Access Token
 *    - GEMINI_API_KEY    : 您的 Google Gemini API Key (可從 Google AI Studio 免費取得)
 * 4. 點選「部署 (Deploy)」->「新增部署 (New deployment)」
 *    - 種類選擇：網頁應用程式 (Web App)
 *    - 執行身分：我 (Me)
 *    - 誰可以存取：任何人 (Anyone)
 * 5. 複製生成的 Webhook URL，填入 LINE Developers Console 的 Webhook URL 即可！
 */

// 讀取設定屬性
function getProps() {
  const props = PropertiesService.getScriptProperties();
  return {
    lineToken: props.getProperty('LINE_ACCESS_TOKEN') || '',
    geminiKey: props.getProperty('GEMINI_API_KEY') || ''
  };
}

// 接收 LINE Webhook POST 請求
function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return ContentService.createTextOutput(JSON.stringify({ status: 'no_content' }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    const events = JSON.parse(e.postData.contents).events;
    if (!events || events.length === 0) {
      return ContentService.createTextOutput(JSON.stringify({ status: 'ok' }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    for (let i = 0; i < events.length; i++) {
      handleEvent(events[i]);
    }

    return ContentService.createTextOutput(JSON.stringify({ status: 'success' }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    console.error('doPost error: ' + err.toString());
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// 接收 GET 請求（健康檢查用）
function doGet(e) {
  return ContentService.createTextOutput('LINE Bot x Google Apps Script x Gemini AI 服務運作正常！');
}

// 事件處理入口
function handleEvent(event) {
  const replyToken = event.replyToken;
  if (!replyToken || replyToken === '00000000000000000000000000000000') {
    return; // 忽略驗證用的 dummy token
  }

  // 1. 好友追蹤事件 (Follow)
  if (event.type === 'follow') {
    const welcomeMsg = "🎉 歡迎加入！我是結合 Google Gemini AI 與 Google Apps Script 的智慧 LINE 夥伴 ✨\n\n您可以直接跟我聊天或詢問任何問題，我會為您提供最精準的回答！\n輸入「/help」可查看指令選單。";
    replyLineMessage(replyToken, [
      { type: 'text', text: welcomeMsg },
      { type: 'sticker', packageId: '11537', stickerId: '52002734' }
    ]);
    return;
  }

  // 2. 貼圖訊息 (Sticker)
  if (event.type === 'message' && event.message.type === 'sticker') {
    const stickerReplies = [
      { text: "收到你的可愛貼圖囉！我也回傳一個給你～ ✨", pkg: "11537", stk: "52002735" },
      { text: "哈哈這貼圖太生動了！讚啦 👍", pkg: "446", stk: "1988" },
      { text: "元氣滿滿！收到你的活力貼圖 ⚡", pkg: "11537", stk: "52002739" }
    ];
    const pick = stickerReplies[Math.floor(Math.random() * stickerReplies.length)];
    replyLineMessage(replyToken, [
      { type: 'text', text: pick.text },
      { type: 'sticker', packageId: pick.pkg, stickerId: pick.stk }
    ]);
    return;
  }

  // 3. 文字訊息 (Text)
  if (event.type === 'message' && event.message.type === 'text') {
    const userText = event.message.text.trim();
    const userLower = userText.toLowerCase();

    // 系統預設快捷指令
    if (userLower === '/help' || userLower === 'help' || userLower === '幫助' || userLower === '功能') {
      const helpText = "🤖 【LINE Bot × Gemini AI 指南】\n─────────────────────────────\n🧠 智慧對話（直接發問）：\n  支援各類日常問題、程式解惑、文章摘要、翻譯創作等，由 Google Gemini AI 驅動！\n\n⚙️ 快捷指令：\n  • /date : 查詢即時日期時間\n  • /joke : 聽個冷笑話\n  • 傳送貼圖 : 機器人互動回貼圖\n  • /help : 查看此指南選單";
      replyLineMessage(replyToken, [{ type: 'text', text: helpText }]);
      return;
    }

    if (userLower === '/date' || userLower === '現在幾點' || userLower === '日期') {
      const nowStr = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");
      replyLineMessage(replyToken, [{ type: 'text', text: "📅 現在時間是 (台灣時區)：\n" + nowStr }]);
      return;
    }

    if (userLower === '/joke' || userLower === '講笑話') {
      const jokes = [
        "有一天，綠豆跳樓變成了什麼？……紅豆，因為流血了！😆",
        "什麼動物最容易摔倒？……狐狸，因為牠狡猾（腳滑）！🦊",
        "小明吃了牛肉麵，為什麼還是覺得很餓？……因為那是牛肉「麵」，不是牛肉「飯」！🍜"
      ];
      const joke = jokes[Math.floor(Math.random() * jokes.length)];
      replyLineMessage(replyToken, [
        { type: 'text', text: "🎭 來個冷笑話放鬆一下：\n\n" + joke },
        { type: 'sticker', packageId: '11537', stickerId: '52002738' }
      ]);
      return;
    }

    // 呼叫 Gemini AI 生成高品質回答
    const aiResponse = callGeminiAI(userText);
    replyLineMessage(replyToken, [{ type: 'text', text: aiResponse }]);
  }
}

// 呼叫 Google Gemini API
function callGeminiAI(prompt) {
  const config = getProps();
  if (!config.geminiKey) {
    return "⚠️ 尚未設定 GEMINI_API_KEY。請先至 Google Apps Script 專案屬性中填入 Gemini API 金鑰！";
  }

  // 支援 gemini-1.5-flash 或 gemini-2.0-flash
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=' + config.geminiKey;

  const systemInstruction = "你是一位親切、聰明、條理清晰且富有同理心的 LINE 聊天助理。請一律使用繁體中文（台灣習慣用語）回答。回答內容力求準確、結構清晰、重點分明，適當使用 emoji 讓對話更生動。";

  const payload = {
    contents: [
      {
        role: "user",
        parts: [{ text: prompt }]
      }
    ],
    systemInstruction: {
      parts: [{ text: systemInstruction }]
    },
    generationConfig: {
      temperature: 0.7,
      maxOutputTokens: 800
    }
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const code = response.getResponseCode();
    const result = JSON.parse(response.getContentText());

    if (code === 200 && result.candidates && result.candidates.length > 0) {
      const candidate = result.candidates[0];
      if (candidate.content && candidate.content.parts && candidate.content.parts.length > 0) {
        return candidate.content.parts[0].text.trim();
      }
    }

    console.error('Gemini API Error (' + code + '): ' + response.getContentText());
    if (code === 400 || code === 403) {
      return "抱歉，Gemini API 認證失敗，請檢查 API Key 是否正確或具備存取權限。";
    }
    return "抱歉，Gemini AI 暫時無法處理您的請求，請稍候再試！";
  } catch (err) {
    console.error('callGeminiAI Exception: ' + err.toString());
    return "連線至 Gemini AI 時發生錯誤，請稍後重試。";
  }
}

// 回傳 LINE 訊息
function replyLineMessage(replyToken, messages) {
  const config = getProps();
  if (!config.lineToken) {
    console.error('LINE_ACCESS_TOKEN is missing!');
    return;
  }

  const url = 'https://api.line.me/v2/bot/message/reply';
  const payload = {
    replyToken: replyToken,
    messages: messages
  };

  const options = {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + config.lineToken
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const res = UrlFetchApp.fetch(url, options);
    console.log('LINE Reply Status: ' + res.getResponseCode());
  } catch (e) {
    console.error('replyLineMessage Error: ' + e.toString());
  }
}
