import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import chat_engine

client = TestClient(app)

def test_root_endpoint():
    """測試根目錄狀態端點"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["callback_endpoint"] == "/callback"

def test_health_endpoint():
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "credentials_configured" in data

def test_callback_without_signature():
    """測試未帶簽章發送 Webhook 請求應回傳 400"""
    response = client.post("/callback", content="{}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing X-Line-Signature header"

def test_callback_with_invalid_signature():
    """測試帶無效簽章發送 Webhook 請求應被拒絕 400"""
    headers = {"X-Line-Signature": "invalid_signature_test"}
    response = client.post("/callback", content='{"events":[]}', headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"

def test_chat_engine_styles():
    """測試風格切換機制"""
    user_id = "test_user_001"
    assert chat_engine.get_user_style(user_id) == "normal"

    # 切換為傲嬌
    res = chat_engine.set_user_style(user_id, "tsundere")
    assert "傲嬌風" in res
    assert chat_engine.get_user_style(user_id) == "tsundere"

    # 傲嬌問候
    reply, sticker = chat_engine.process_smart_chat("早安", user_id)
    assert "哼" in reply
    assert sticker is not None

def test_chat_engine_mini_features():
    """測試生活趣味小工具 (笑話/運勢/美食)"""
    user_id = "test_user_002"

    # 笑話
    joke_text, joke_stk = chat_engine.process_smart_chat("講笑話", user_id)
    assert "冷笑話" in joke_text
    assert joke_stk == chat_engine.STICKERS["laugh"]

    # 運勢
    fortune_text, fortune_stk = chat_engine.process_smart_chat("今日運勢", user_id)
    assert "今日運勢占卜" in fortune_text
    assert fortune_stk is not None

    # 美食
    food_text, food_stk = chat_engine.process_smart_chat("吃什麼", user_id)
    assert "靈感推薦" in food_text
    assert food_stk is not None

def test_sticker_response_generation():
    """測試收到貼圖時產生貼圖回覆"""
    reply_text, sticker_info = chat_engine.build_sticker_response()
    assert len(reply_text) > 0
    assert len(sticker_info) == 2
    pkg_id, stk_id = sticker_info
    assert isinstance(pkg_id, str) and isinstance(stk_id, str)
