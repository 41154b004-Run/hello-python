import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.responses import PlainTextResponse, JSONResponse
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration

from app import config
from app.handlers import register_handlers

# 設定記錄日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("line-bot")

# 初始化 LINE SDK 組態
configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

# 註冊事件處理器
register_handlers(handler, configuration)


@asynccontextmanager
async def lifespan(app: FastAPI):
    missing_creds = config.check_credentials()
    if missing_creds:
        logger.warning(
            "LINE credentials missing: %s. Please configure in .env.",
            ", ".join(missing_creds)
        )
    else:
        logger.info("LINE credentials loaded successfully.")
    yield
    logger.info("LINE Bot server shutting down...")


app = FastAPI(
    title="Python LINE Bot API",
    description="基於 FastAPI 與 line-bot-sdk v3 開發的 LINE 機器人後端服務",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_class=JSONResponse)
async def root():
    """根目錄端點：確認伺服器運作正常"""
    return {
        "status": "online",
        "service": "Python LINE Bot",
        "version": "1.0.0",
        "callback_endpoint": "/callback"
    }


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """健康檢查端點"""
    missing_creds = config.check_credentials()
    return {
        "status": "healthy",
        "credentials_configured": len(missing_creds) == 0,
        "missing_credentials": missing_creds
    }


@app.post("/callback", response_class=PlainTextResponse)
async def callback(request: Request, x_line_signature: str = Header(None)):
    """
    LINE Webhook 接收點
    LINE 官方伺服器會將使用者事件 POST 至此端點
    """
    if not x_line_signature:
        logger.warning("收到未包含 X-Line-Signature 標頭的請求。")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Line-Signature header"
        )

    # 取得原始請求內容二進位字串（簽章驗證必須使用 raw body）
    body = (await request.body()).decode("utf-8")

    try:
        # 驗證簽章並分發事件
        handler.handle(body, x_line_signature)
    except InvalidSignatureError:
        logger.error("簽章驗證失敗 (InvalidSignatureError)！請確認 Channel Secret 是否正確。")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    except Exception as e:
        logger.exception("處理 Webhook 事件時發生未預期錯誤: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

    return "OK"
