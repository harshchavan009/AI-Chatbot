import logging
import sys

def setup_logging():
    """
    Setup logging configuration for the AI Chatbot.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("chatbot.log")
        ]
    )
    return logging.getLogger("ai_chatbot")

logger = setup_logging()
