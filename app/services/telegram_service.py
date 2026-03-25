import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from app.core.config import settings
from app.api.endpoints import openai_service
from app.core.logging import logger

class TelegramBot:
    """
    Telegram Bot integration for the AI Chatbot.
    """
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /start command.
        """
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Hello! I am your AI Chatbot. How can I help you today?"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming messages.
        """
        user_input = update.message.text
        chat_id = str(update.effective_chat.id)
        
        logger.info(f"Telegram message received from {chat_id}: {user_input}")
        
        # Get response from OpenAI service
        response = await openai_service.get_response(chat_id, user_input)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response
        )

    def run(self):
        """
        Run the bot.
        Note: In a production environment, you might want to run this in a 
        separate process or thread if integrated with FastAPI, OR use webhooks.
        """
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not provided. Telegram integration disabled.")
            return

        self.application = ApplicationBuilder().token(self.token).build()
        
        start_handler = CommandHandler('start', self.start)
        msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message)
        
        self.application.add_handler(start_handler)
        self.application.add_handler(msg_handler)
        
        logger.info("Starting Telegram Bot...")
        self.application.run_polling()

telegram_bot = TelegramBot()
