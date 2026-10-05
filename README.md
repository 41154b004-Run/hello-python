# Python LINE Bot 專案

本專案使用 **Python 3.12**、**FastAPI** 與最新的 **LINE Bot SDK (v3)** 所建置的 LINE 聊天機器人後端服務。

---

## 專案功能特色

- ⚡ **高效能非同步後端**：基於 FastAPI 與 Uvicorn，具備優異回應速度與自動生成的 API 文件。
- 🛡️ **標準安全簽章驗證**：嚴格驗證 LINE 官方的 `X-Line-Signature`，防止未授權與偽造請求。
- 💬 **多功能指令分發**：
  - `/help` 或 `指令`：查看所有指令清單。
  - `/date` 或 `日期`：取得伺服器動態日期與時間。
  - `/countdown [秒數]` 或 `倒數`：自訂秒數倒數計時（預設 3 秒）。
  - `/card` 或 `卡片`：展示精美的 LINE **Flex Message** 卡片。
  - **一般對話**：自動回音 (Echo) 與功能提示。
- 🤝 **好友事件處理**：使用者加入好友時發送個人化歡迎訊息。
- 🧪 **完整單元測試**：包含端點回應與簽章驗證測試。

---

## 目錄架構

```text
0921test/
├── app/
│   ├── __init__.py
│   ├── config.py         # 環境變數與設定讀取
│   ├── handlers.py       # LINE 訊息與事件分發邏輯
│   └── main.py           # FastAPI Webhook 伺服器主入口
├── tests/
│   └── test_app.py       # 自動化測試腳本
├── .env.example          # 環境變數範例檔
├── .gitignore            # Git 忽略設定（避免金鑰外洩）
├── requirements.txt      # 相依套件清單
├── run.py                # 快速啟動腳本
└── README.md             # 專案說明文件
```

---

## 快速開始指南

### 1. 建立 `.env` 環境變數檔

複製範本檔案建立 `.env`：
```powershell
Copy-Item .env.example .env
```

開啟 `.env` 並填入您的 LINE Channel 資訊：
```ini
LINE_CHANNEL_ACCESS_TOKEN=您的_Channel_Access_Token
LINE_CHANNEL_SECRET=您的_Channel_Secret
PORT=8000
```

> [!TIP]
> **如何取得 LINE 金鑰？**
> 1. 登入 [LINE Developers Console](https://developers.line.biz/)。
> 2. 建立一個 Provider（若尚未建立），並在其中建立一個 **Messaging API** Channel。
> 3. 在 **Basic settings** 分頁中找到 **Channel secret**。
> 4. 在 **Messaging API** 分頁最下方發行 **Channel access token (long-lived)**。

---

### 2. 啟動機器人伺服器

執行下列指令啟動本機伺服器：
```powershell
python run.py
```
啟動後會顯示：
```text
🚀 正在啟動 Python LINE Bot 服務，監聽位址：http://0.0.0.0:8000
👉 本地測試端點：http://127.0.0.1:8000/
👉 Webhook 回呼網址：http://127.0.0.1:8000/callback
```
您可在瀏覽器開啟 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 查看互動式 Swagger API 文件。

---

### 3. 本地測試與 LINE 串接 (透過 ngrok)

由於 LINE 官方伺服器需要公開且具備 HTTPS 的網址才能將訊息推送到您的電腦，測試時建議使用 **ngrok**：

1. 下載並安裝 [ngrok](https://ngrok.com/)。
2. 在新終端機執行：
   ```powershell
   ngrok http 8000
   ```
3. 複製 ngrok 產生的 HTTPS Forwarding 網址（例如：`https://xxxx-xx-xx.ngrok-free.app`）。
4. 前往 [LINE Developers Console](https://developers.line.biz/) 的 **Messaging API** 分頁：
   - **Webhook URL** 填入：`https://xxxx-xx-xx.ngrok-free.app/callback`
   - 開啟 **Use webhook**
   - 點擊 **Verify**，顯示 `Success` 即表示連線成功！
5. 在 LINE 官方帳號設定中關閉「自動回應訊息」（避免 LINE 官方系統與您的 Bot 重複回話）。
6. 用手機掃描 QR Code 加入好友，開始體驗！

---

### 4. 執行自動化測試

```powershell
python -m pytest
```
此測試會驗證 Webhook 的安全簽章拒絕機制與各 API 端點運作。
