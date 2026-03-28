# 🤖 Production-Ready AI Chatbot

A high-performance, modular, and scalable AI Chatbot built with **FastAPI**, **OpenAI API**, and **Telegram Bot API**. Featuring a premium web interface and session-based chat history.

## 🚀 Features

- **Real-time Interaction:** Fast and responsive chat using FastAPI and asynchronous operations.
- **AI-Powered:** Integrated with OpenAI's `gpt-3.5-turbo` for natural language understanding.
- **Context-aware:** Maintains conversation history per session (browser/Telegram).
- **Multichannel:** Access the bot via a premium web UI or Telegram.
- **Production-Ready:** Modular architecture, clean code, logging, and error handling.
- **Auto-Documentation:** Built-in Swagger UI and ReDoc via FastAPI.

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **AI Integration:** OpenAI API
- **Bot Integration:** Python-Telegram-Bot API
- **Frontend:** Vanilla HTML, CSS (Premium Design), JS
- **Environment:** Python-dotenv, Pydantic Settings
- **Logging:** Python Logging Module

---

## 🏗️ Project Structure

```text
Chatbot/
├── app/
│   ├── api/            # API endpoints & Pydantic models
│   ├── core/           # Configuration & Logging
│   ├── services/       # OpenAI & Telegram bot logic
│   └── static/         # Frontend (HTML, CSS, JS)
├── .env                # Environment variables (Internal)
├── .env.example        # Template for environment variables
├── main.py             # FastAPI entry point
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
```

---

## 🚦 Getting Started

### 1. Prerequisites
- Python 3.8+
- OpenAI API Key
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd Chatbot

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env` and fill in your API keys:
```bash
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
```

### 4. Running the App
```bash
# Start the FastAPI server
python -m app.main
```
The app will be available at `http://localhost:8000`.

---

## 🌐 API Documentation

Once the server is running, you can access:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🚢 Deployment (Docker / Railway / Render)

### Running with Docker (Recommended for Local & Server)

The easiest way to run the chatbot is using Docker and Docker Compose.

1. **Pre-requisites:** Install Docker and Docker Compose.
2. **Environment Setup:** Ensure you have a `.env` file with your `OPENAI_API_KEY` and `TELEGRAM_BOT_TOKEN`.
3. **Run the Chatbot:**
   ```bash
   docker-compose up --build -d
   ```
4. **Access the Chatbot:**
   - **Web UI:** `http://localhost:8000`
   - **Telegram Bot:** Check your bot on Telegram.
5. **Stop the Chatbot:**
   ```bash
   docker-compose down
   ```

### Render Deployment
1. Connect your GitHub repository to Render.
2. Create a new **Web Service**.
3. Set the **Build Command** to: `pip install -r requirements.txt`
4. Set the **Start Command** to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add your `.env` variables in the Render "Environment" settings.

### Railway Deployment
1. Connect your GitHub repository to Railway.
2. Railway will automatically detect the `Procfile` (if added) or you can use the default Python start command.
3. Add your Environment Variables in the "Variables" tab.

---

## 🧪 Testing

To test the chatbot:
1. Open `http://localhost:8000` in your browser.
2. Send a message to your Telegram Bot.
3. Check the `chatbot.log` file for logs.

---

## 📜 License
MIT License. Free to use and modify.
