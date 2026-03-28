# Deployment Guide: Nova AI Chatbot

Follow this guide to move your Nova AI Chatbot from `localhost` to a live, working server.

---

## 1. Prerequisites
- A **MongoDB Atlas** account (Free tier is fine).
- API Keys for **Google Gemini** (recommended) or **OpenAI**.
- A **Telegram Bot Token** (if using the Telegram integration).

## 2. Setting up Cloud Database (MongoDB Atlas)
1. Sign up at [mongodb.com](https://www.mongodb.com/cloud/atlas).
2. Create a new cluster (Shared/Free tier).
3. Create a **Database User** (with read/write access).
4. **Network Access**: Add IP `0.0.0.0/0` (to allow access from anywhere, or restrict it to your server's IP).
5. Get your **Connection String** (URI) and replace the placeholders in your `.env`:
   ```env
   MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/chatbot_db
   ```

---

## 3. Option A: Deploy to Render (Recommended)
Render is the easiest way to host FastAPI apps with a Dockerfile.

1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Select **Docker** as the Runtime.
4. **Environment Variables**: Add all variables from your `.env`:
   - `MONGODB_URL`
   - `GEMINI_API_KEY`
   - `PRODUCTION=true`
   - `SECRET_KEY` (Generate a strong one)
5. Render will automatically build and deploy your app. Your live URL will look like `https://your-app-name.onrender.com`.

---

## 4. Option B: Deploy to Railway
Railway is similar to Render and very fast.

1. New Project -> **Deploy from GitHub repo**.
2. Railway will detect the `Dockerfile`.
3. Go to **Variables** tab and add your `.env` content.
4. Railway will provide a public URL automatically.

---

## 5. Option C: Self-Hosted VPS (Docker Compose)
If you have a Linux server (Ubuntu/Debian) with Docker installed:

1. Clone your repo to the server.
2. Create a `.env` file on the server.
3. Run:
   ```bash
   docker-compose up -d --build
   ```
4. Access your AI on `http://your-server-ip:8000`.

---

## 6. Post-Deployment Checklist
- [ ] **Verify SSL**: Ensure you are using `https`. Render/Railway provide this for free.
- [ ] **Restrict CORS**: (Optional) In `app/main.py`, you can change `allow_origins=["*"]` to your specific domain for better security.
- [ ] **Telegram Webhook**: If using Telegram, your server must be live and reachable for the bot to communicate (though the current script uses polling, which works anywhere with internet).

---

**Success!** Your AI Chatbot is now live and ready to serve users across the globe. 🚀
