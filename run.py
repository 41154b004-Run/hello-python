import sys
import uvicorn
from app import config

if __name__ == "__main__":
    print(f"Starting Python LINE Bot on http://0.0.0.0:{config.PORT}")
    print(f"Local test URL: http://127.0.0.1:{config.PORT}/")
    print(f"Webhook callback URL: http://127.0.0.1:{config.PORT}/callback")
    print("-" * 60)
    uvicorn.run("app.main:app", host="0.0.0.0", port=config.PORT)
