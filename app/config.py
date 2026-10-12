import os
from pathlib import Path
from dotenv import load_dotenv

# 載入專案根目錄下的 .env 檔案
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "").strip()
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1").strip()
DIFY_MCP_URL = os.getenv("DIFY_MCP_URL", "").strip()
PORT = int(os.getenv("PORT", 8000))

def check_credentials():
    """檢查 LINE 金鑰設定是否完整"""
    missing = []
    if not LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_ACCESS_TOKEN == "your_channel_access_token_here":
        missing.append("LINE_CHANNEL_ACCESS_TOKEN")
    if not LINE_CHANNEL_SECRET or LINE_CHANNEL_SECRET == "your_channel_secret_here":
        missing.append("LINE_CHANNEL_SECRET")
    return missing
