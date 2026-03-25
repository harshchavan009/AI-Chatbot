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
import google.generativeai as genai

router = APIRouter()

# --- AI Service Logic (Unified into API Layer) ---
class ChatService:
    def __init__(self):
        # OpenAI Setup
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_client = AsyncOpenAI(api_key=self.openai_key) if self.openai_key and "..." not in self.openai_key and "your_" not in self.openai_key else None
        
        # Gemini Setup
        self.gemini_key = settings.GEMINI_API_KEY
        self.gemini_enabled = False
        if self.gemini_key and "..." not in self.gemini_key and "your_" not in self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_enabled = True
            except Exception as e:
                logger.error(f"Gemini configuration error: {str(e)}")
        
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

        # 1. Try OpenAI if available and not in Mock Mode
        if self.openai_client and not settings.MOCK_MODE:
            try:
                messages = self.sessions[session_id][-20:]
                system_instruction = (
                    f"You are a highly intelligent AI Assistant. You MUST respond in {language}. "
                    "Provide detailed, accurate, and reasoned answers. For complex questions, "
                    "think step-by-step to ensure correctness."
                )
                messages.insert(0, {"role": "system", "content": system_instruction})
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7
                )
                assistant_message = response.choices[0].message.content
                self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
                return assistant_message
            except Exception as e:
                logger.error(f"OpenAI error: {str(e)}")
                # Fall through to Gemini or Mock

        # 2. Try Gemini if available (even in Mock Mode if OpenAI is missing)
        if self.gemini_enabled:
            try:
                # Upgraded to gemini-1.5-flash for better reasoning and speed
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Convert history to Gemini format
                history = []
                for msg in self.sessions[session_id][:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    history.append({"role": role, "parts": [msg["content"]]})
                
                chat = model.start_chat(history=history)
                
                # Enhanced reasoning prompt for Gemini
                gemini_input = (
                    f"Current Language: {language}. "
                    "Instruction: You are a highly intelligent AI. Provide a detailed, "
                    "step-by-step reasoned answer if the question is complex. "
                    f"Responda en {language}. "
                    f"User message: {user_input}"
                )
                
                response = await chat.send_message_async(gemini_input)
                assistant_message = response.text
                self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
                return assistant_message
            except Exception as e:
                logger.error(f"Gemini error: {str(e)}")
                # Fall through to Mock

        # 3. Fallback / Enhanced Search for Complex Questions
        logger.info(f"Using enhanced knowledge search for: {user_input[:50]}... in {language}")
        
        # Determine if we should perform a web search for better context
        search_triggers = ["who", "what", "where", "when", "how", "current", "news", "latest", "price", "vs"]
        should_search = any(trigger in user_input.lower() for trigger in search_triggers)
        
        search_context = ""
        if should_search:
            try:
                url = f"https://api.duckduckgo.com/?q={user_input}&format=json&no_html=1"
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("AbstractText"):
                                search_context = data["AbstractText"]
            except Exception as e:
                logger.error(f"Search error: {str(e)}")

        # Check direct smart answers first
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
            "correct": "To make me answer every question correctly, please add a valid OpenAI API key or Gemini API key in the .env file!"
        }

        for key, val in smart_answers.items():
            if key in prompt_lower:
                assistant_message = val
                if language != "English":
                    assistant_message = f"(Mock Response in English, Language selected: {language})\n\n" + assistant_message
                self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
                return assistant_message

        # If we got search context, use it to provide a better mock response
        if search_context:
            assistant_message = f"Based on my research: {search_context}\n\n(This is an enhanced search result for your complex question.)"
            if language != "English":
                assistant_message = f"(Language selected: {language})\n\n" + assistant_message
            self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
            return assistant_message

        # Conversational fallbacks
        input_preview = str(user_input)[:20]
        conversational_responses = [
            f"That's an interesting question about '{input_preview}'. In Demo Mode, I can tell you that this project is built with FastAPI and designed for high performance!",
            f"I'm currently operating in Demo Mode, but I'd love to discuss '{input_preview}' once you've added an AI API key (OpenAI or Gemini) to my configuration.",
            f"As an AI Assistant in Demo Mode, I have limited knowledge on '{input_preview}'. However, I'm fully capable of complex reasoning with a valid API key!",
            f"I see you're asking about '{input_preview}'. While I'm in Demo Mode, I'm focusing on showcasing my premium UI and backend architecture."
        ]
        import random
        assistant_message = random.choice(conversational_responses)
        if language != "English":
            assistant_message = f"(Language selected: {language})\n\n" + assistant_message
        self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
        return assistant_message

# Initialize the service instance
chat_service = ChatService()

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
        response_text = await chat_service.get_response(request.session_id or "default_session", request.user_input, request.language or "English")
        return ChatResponse(
            response=response_text,
            session_id=request.session_id or "default_session"
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
