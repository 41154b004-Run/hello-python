import pytest
from fastapi.testclient import TestClient
from app.main import app

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
