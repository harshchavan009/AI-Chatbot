from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import openai
from openai import AsyncOpenAI
import aiohttp
from app.services.auth_service import auth_service
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

# --- AI Service Logic (Unified into API Layer) ---
class OpenAIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key and "..." not in self.api_key and "your_" not in self.api_key else None
        self.sessions: Dict[str, List[Dict[str, str]]] = {}

    async def get_response(self, session_id: str, user_input: str, language: str = "English"):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        # Add a system-like instruction if language is not English
        if language != "English":
            user_input_with_lang = f"[Please respond in {language}] {user_input}"
        else:
            user_input_with_lang = user_input

        self.sessions[session_id].append({"role": "user", "content": user_input_with_lang})

        # Fallback for demonstration if key is missing or explicitly in mock mode
        if not self.client or settings.MOCK_MODE:
            logger.info(f"Using smart knowledge search for: {user_input[:50]}... in {language}")
            
            # 1. Check direct smart answers first (Note: results are in English, but we could translate them if needed)
            # For simplicity, we'll keep the mock answers in English but inform the user.
            prompt_lower = user_input.lower()
            smart_answers = {
                "tech stack": "My tech stack includes Python, FastAPI, Uvicorn, OpenAI API, and a premium Vanilla HTML/CSS/JS frontend. It's designed for scalability and speed.",
                "features": "I feature JWT authentication, session-based chat history, a logging system, Telegram Bot integration, and a multi-language support system.",
                "deploy": "You can deploy me easily to Render, Railway, or Heroku using the provided Procfile and requirements.txt. I'm ready for production!",
                "who are you": "I am a production-ready AI Chatbot designed to showcase professional backend and frontend development skills. I can assist with coding, tech questions, and more.",
                "fastapi": "FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. It's one of the fastest Python frameworks available.",
                "python": "Python is a high-level, interpreted, general-purpose programming language. Its design philosophy emphasizes code readability and simplicity.",
                "django": "Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. It's 'batteries-included' and very secure.",
                "dsa": "Data Structures and Algorithms (DSA) are the building blocks of efficient software development. Understanding them is key to writing optimized code.",
                "java": "Java is a high-level, class-based, object-oriented programming language that is designed to have as few implementation dependencies as possible. 'Write once, run anywhere'!",
                "javascript": "JavaScript is a versatile, high-level, often just-in-time compiled language that is one of the core technologies of the World Wide Web.",
                "html": "HTML (HyperText Markup Language) is the standard markup language for documents designed to be displayed in a web browser.",
                "css": "CSS (Cascading Style Sheets) is a style sheet language used for describing the presentation of a document written in a markup language like HTML.",
                "sql": "SQL (Structured Query Language) is a standard language for managing and manipulating relational databases.",
                "git": "Git is a distributed version-control system for tracking changes in source code during software development.",
                "react": "React is a free and open-source front-end JavaScript library for building user interfaces based on components.",
                "hello": "Hello! I am your AI Assistant. How can I help you today?",
                "hi": "Hi there! How can I assist you today?",
                "correct": "To make me answer every question correctly, please add a valid OpenAI API key in the .env file and set MOCK_MODE to false!"
            }

            for key, val in smart_answers.items():
                if key in prompt_lower:
                    assistant_message = val
                    if language != "English":
                        assistant_message = f"(Mock Response in English, Language selected: {language})\n\n" + assistant_message
                    self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
                    return assistant_message

            # 2. Try DuckDuckGo Abstract API (Free, No Key)
            try:
                url = f"https://api.duckduckgo.com/?q={user_input}&format=json&no_html=1"
                # Added SSL verification bypass for demo mode if needed, and better error handling
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("AbstractText"):
                                assistant_message = data["AbstractText"]
                                if language != "English":
                                    assistant_message = f"(Mock Response in English, Language selected: {language})\n\n" + assistant_message
                                self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
                                return assistant_message
            except Exception as e:
                logger.error(f"Search fallback error: {str(e)}")

            # 3. Default conversational fallbacks
            conversational_responses = [
                f"That's an interesting question about '{user_input[:30]}'. In Demo Mode, I can tell you that this project is built with FastAPI and designed for high performance!",
                f"I'm currently operating in Demo Mode, but I'd love to discuss '{user_input[:20]}' once you've added an OpenAI API key to my configuration.",
                f"As an AI Assistant in Demo Mode, I have limited knowledge on '{user_input[:20]}'. However, I'm fully capable of complex reasoning with a valid API key!",
                f"I see you're asking about '{user_input[:20]}'. While I'm in Demo Mode, I'm focusing on showcasing my premium UI and backend architecture."
            ]
            import random
            assistant_message = random.choice(conversational_responses)
            if language != "English":
                assistant_message = f"(Language selected: {language})\n\n" + assistant_message
            self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
            return assistant_message

        try:
            # For real OpenAI calls, we can prepend a system message or just the instruction
            messages = self.sessions[session_id][-20:]
            
            # Ensure the AI knows the language preference
            messages.insert(0, {"role": "system", "content": f"You are a helpful assistant. You MUST respond in {language}."})
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            assistant_message = response.choices[0].message.content
            self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            return "I'm sorry, I'm having trouble connecting to my brain right now. Please check if your API key is correctly configured!"

# Initialize the service instance
openai_service = OpenAIService()

# --- API Endpoints ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    """
    Model for chat request.
    """
    user_input: str
    session_id: Optional[str] = "default_session"
    language: Optional[str] = "English"

class ChatResponse(BaseModel):
    """
    Model for chat response.
    """
    response: str
    session_id: str

@router.post("/signup")
async def signup(user: UserCreate):
    if user.username in auth_service.users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth_service.get_password_hash(user.password)
    auth_service.users_db[user.username] = {"password": hashed_password}
    return {"message": "User created successfully"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.users_db.get(form_data.username)
    if not user or not auth_service.verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth_service.create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    username = auth_service.decode_access_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return username

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: str = Depends(get_current_user)):
    """
    Endpoint for real-time chatbot interaction (Protected).
    """
    logger.info(f"Received chat request from user {current_user}, session: {request.session_id}, language: {request.language}")
    try:
        response_text = await openai_service.get_response(request.session_id or "default_session", request.user_input, request.language or "English")
        return ChatResponse(
            response=response_text,
            session_id=request.session_id
        )
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}
