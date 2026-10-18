import logging
from typing import List, Dict

logger = logging.getLogger("line-bot")

# 觸發聯網搜尋的關鍵詞特徵
WEB_SEARCH_TRIGGER_KEYWORDS = [
    "最新", "新聞", "今天", "明天", "最近", "目前", "天氣", "股價",
    "匯率", "今年", "2025", "2026", "誰是", "查詢", "搜尋", "哪裡",
    "多少錢", "賽程", "上映", "評價", "現任", "活動", "推薦", "什麼是",
    "怎麼去", "營業時間", "官網", "地震", "颱風"
]

def should_search_web(query: str) -> bool:
    """判斷使用者提問是否需要連網搜尋最新即時資訊"""
    q = query.strip().lower()
    
    # 明確指定搜尋指令
    if q.startswith(("/search", "/google", "搜尋", "查一下", "找一下")):
        return True
    
    # 含有時效性或即時性關鍵字
    if any(k in q for k in WEB_SEARCH_TRIGGER_KEYWORDS):
        return True
    
    # 詢問疑問句（長度適中且含有問句標記）
    if len(q) >= 4 and any(q.endswith(p) for p in ["？", "?", "嗎", "呢", "嗎？", "嗎?"]):
        return True

    return False

def search_web(query: str, max_results: int = 3) -> str:
    """
    使用 DuckDuckGo 即時搜尋網路資訊並整理成簡短上下文
    """
    clean_query = query.strip()
    for prefix in ["/search", "/google", "搜尋", "查一下", "找一下"]:
        if clean_query.lower().startswith(prefix):
            clean_query = clean_query[len(prefix):].strip()
            break

    if not clean_query:
        return ""

    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(clean_query, max_results=max_results))
            if not results:
                return ""
            
            snippets = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "").strip()
                body = r.get("body", "").strip()
                href = r.get("href", "").strip()
                if title or body:
                    snippets.append(f"[{i}] 標題: {title}\n摘要: {body}\n來源連結: {href}")
            
            return "\n\n".join(snippets)
    except Exception as e:
        logger.warning("Web search error: %s", str(e))
        return ""
