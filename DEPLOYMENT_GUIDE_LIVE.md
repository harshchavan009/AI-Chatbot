# 🚀 Production Deployment Guide

Your AI Chatbot is now production-ready! I have updated the code to handle environmental requirements, cross-origin requests, and health monitoring.

## ✅ Summary of Changes
1.  **Frontend**: Added `API_BASE_URL` in `script.js` for flexible backend connections.
2.  **Backend**: Added a root `/health` endpoint for monitoring.
3.  **Security**: Implemented configurable CORS (Cross-Origin Resource Sharing).
4.  **Configuration**: Optimized `PORT` handling for cloud environments (Render/Railway).
5.  **Logging**: Enhanced startup/shutdown logging for production debugging.

---

## 🛠️ Deployment Steps (Render.com)

### 1. Prepare your Repository
Make sure your latest changes are pushed to GitHub:
```bash
git add .
git commit -m "Deployment ready: Added health checks and CORS"
git push origin main
```

### 2. Create a Web Service on Render
1.  Log in to [Render.com](https://render.com).
2.  Click **New +** and select **Web Service**.
3.  Connect your GitHub repository.
4.  **Runtime**: Python
5.  **Build Command**: `pip install -r requirements.txt`
6.  **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3. Configure Environment Variables
In the **Environment** tab on Render, add the following:
*   `GEMINI_API_KEY`: Your Google Gemini API Key.
*   `MONGODB_URL`: Your MongoDB connection string (or use the built-in MockDB if not using MongoDB).
*   `APP_NAME`: `Nova AI Chatbot`
*   `PRODUCTION`: `true`
*   `ALLOWED_ORIGINS`: `*` (or your specific frontend domain for higher security).

### 4. Health Check
Render will automatically use the `/health` endpoint I added to verify that your server is running correctly before switching traffic to the new version.

---

## 🛠️ Deployment Steps (Railway.app)

1.  Connect your GitHub repo to Railway.
2.  Railway will automatically detect the `Procfile` and use the start command:
    `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3.  Go to **Variables** and add your `GEMINI_API_KEY` and other vars.

---

## 📝 Project Details
*   **Health Check URL**: `https://your-app-name.onrender.com/health`
*   **Main Chat UI**: `https://your-app-name.onrender.com/`
*   **API Docs**: `https://your-app-name.onrender.com/docs`
