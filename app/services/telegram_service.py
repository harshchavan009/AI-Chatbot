import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from app.core.config import settings
from app.api.endpoints import chat_service
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
        
        # Get response from the unified ChatService
        response, image_url = await chat_service.get_response(chat_id, user_input, language="English")
        
        # Send text response
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response
        )

        # Send photo if available
        if image_url:
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=image_url,
                    caption=f"Related photo for: {user_input[:50]}..."
                )
            except Exception as e:
                logger.error(f"Failed to send photo to Telegram: {str(e)}")

    def run(self):
        """
        Run the bot with a token validity check.
        """
        if not self.token or self.token == "...":
            logger.warning("TELEGRAM_BOT_TOKEN is missing or placeholder. Telegram integration skipped.")
            return

        try:
            self.application = ApplicationBuilder().token(self.token).build()
            
            start_handler = CommandHandler('start', self.start)
            msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message)
            
            self.application.add_handler(start_handler)
            self.application.add_handler(msg_handler)
            
            logger.info("Starting Telegram Bot...")
            # Use a slightly more robust way to run that can be interrupted
            self.application.run_polling(stop_signals=None) 
        except Exception as e:
            if "InvalidToken" in str(e) or "404" in str(e):
                logger.warning(f"Telegram Bot failed to start: Invalid Token. Web UI will continue to work.")
            else:
                logger.error(f"Telegram Bot error: {str(e)}")

telegram_bot = TelegramBot()
