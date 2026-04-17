import subprocess
import sys
import os
import time
from app.core.config import settings

def run_live():
    # 1. Start FastAPI server
    port = str(settings.PORT)
    host = "0.0.0.0"
    
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", port]
    
    # Disable reload in production for stability
    if not settings.PRODUCTION and settings.DEBUG:
        cmd.append("--reload")
        print(f"Starting FastAPI server with reload on http://{host}:{port}...")
    else:
        print(f"Starting FastAPI server in PRODUCTION mode on port {port}...")

    fastapi_proc = subprocess.Popen(
        cmd,
        env=os.environ.copy()
    )
    
    # 2. Wait a bit for FastAPI to start
    time.sleep(2)
    
    # 3. Start Telegram Bot
    # Since telegram_bot.run() is blocking, we run it in a separate process or thread
    # But here we can just run it in a separate subprocess
    print("Starting Telegram Bot...")
    telegram_proc = subprocess.Popen(
        [sys.executable, "-c", "from app.services.telegram_service import telegram_bot; telegram_bot.run()"],
        env=os.environ.copy()
    )
    
    print("\nAI Chatbot is now running live!")
    print("Web UI: http://0.0.0.0:8000 (Live Server)")
    print("Telegram Bot: (Check your bot on Telegram)")
    print("\nPress Ctrl+C to stop.")
    
    warned_telegram = False
    try:
        while True:
            time.sleep(1)
            # Only exit if FastAPI dies, as it's the core of the Web UI
            if fastapi_proc.poll() is not None:
                print("FastAPI process exited. Shutting down...")
                break
            
            # If telegram dies, just log it once silently
            if telegram_proc.poll() is not None and not warned_telegram:
                # No more loud warning, just a status note
                # print("Note: Telegram service is currently inactive. Web UI is live.")
                warned_telegram = True
    except KeyboardInterrupt:
        print("\nStopping...")
        fastapi_proc.terminate()
        telegram_proc.terminate()

if __name__ == "__main__":
    run_live()
