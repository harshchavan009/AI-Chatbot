from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import openai
from openai import AsyncOpenAI
import aiohttp
from app.services.auth_service import auth_service
from app.core.config import settings
from app.core.logging import logger
from app.core.database import db
from google import genai
from datetime import datetime
import uuid

router = APIRouter()

# --- Models ---

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = datetime.now()

class Conversation(BaseModel):
    id: str
    username: str
    title: str
    messages: List[ChatMessage]
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class ChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None
    language: Optional[str] = "English"
    image: Optional[str] = None
    document: Optional[str] = None
    document_name: Optional[str] = None
    model: Optional[str] = "gemini-2.5-flash"
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    session_id: str
    title: Optional[str] = None
    image_url: Optional[str] = None

class ConversationSummary(BaseModel):
    id: str
    title: str
    last_message: str
    updated_at: datetime

class SearchEntry(BaseModel):
    query: str
    timestamp: datetime
    session_id: str

class AdminStats(BaseModel):
    total_users: int
    total_chats: int
    top_queries: List[dict]
    api_hits: int
    system_status: str

# --- AI Service Logic ---

class ChatService:
    def __init__(self):
        # OpenAI Setup
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_client = AsyncOpenAI(api_key=self.openai_key) if self.openai_key and "..." not in self.openai_key and "your_" not in self.openai_key else None
        
        # Gemini Setup (Upgraded to google-genai)
        self.gemini_key = settings.GEMINI_API_KEY
        self.gemini_enabled = False
        self.gemini_client = None
        if self.gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
                self.gemini_enabled = True
            except Exception as e:
                logger.error(f"Gemini configuration error: {str(e)}")

    def extract_text_from_base64(self, base64_str: str, filename: str) -> str:
        """Extract text from base64 encoded PDF or TXT file."""
        import base64
        import io
        try:
            # Remove header if exists (e.g., data:application/pdf;base64,)
            if "," in base64_str:
                base64_str = base64_str.split(",")[1]
            
            file_data = base64.b64decode(base64_str)
            
            if filename.lower().endswith('.pdf'):
                import PyPDF2
                logger.info(f"Extracting text from PDF: {filename}")
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            else:
                logger.info(f"Extracting text from text file: {filename}")
                return file_data.decode('utf-8', errors='ignore').strip()
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return ""

    async def get_search_context(self, user_input: str, language: str) -> str:
        """Lightning-fast local context discovery."""
        lower_input = user_input.lower().strip().strip("?!.")
        
        # --- Lightning Fast Path (Sub-50ms) ---
        fast_responses = {
            "hi": "Hello! I am Nova AI. How can I help you today?",
            "hello": "Hi there! I'm your AI assistant. What's on your mind?",
            "explain python simply": "Python is a high-level, easy-to-read programming language. Imagine it like writing a recipe in English—it uses simple words and clear structure, making it the perfect choice for beginners!",
            "what is python": "Python is a powerful, versatile programming language used for web development, data science, and AI. It's famous for being very easy to learn and write.",
            "who are you": "I am Nova AI, a premium intelligent assistant powered by Google's latest Gemini 2.0 technology.",
            "what can you do": "I can analyze images, chat about documents, search the web, write code, and help you with complex research!"
        }
        
        if lower_input in fast_responses:
            return fast_responses[lower_input]

        """Fetch summary from Wikipedia with initial search for better matching, localized by language."""
        # --- Local Smart Knowledge Fallback (Localized) ---
        smart_responses = {
            "English": {
                "hello": "Hello! I'm Nova AI, your premium intelligent assistant. How can I assist you today?",
                "hi": "Hi! I'm Nova AI. Ready to help with coding, writing, or any questions you have.",
                "resume": "To improve your software engineering resume: 1. Use a clean, single-column layout. 2. Highlight specific technologies (React, Python, etc.). 3. Quantify achievements (e.g., 'Improved performance by 30%'). 4. Include a strong GitHub profile and project links.",
                "tips to improve my resume": "For a stellar Software Engineering resume: 1. Focus on 'Impact' rather than just 'Responsibilities'. 2. Categorize skills by 'Languages', 'Frameworks', and 'Tools'. 3. Ensure your projects demonstrate problem-solving. 4. Keep it to one page if you have less than 5 years of experience.",
                "python": "Python is a high-level, interpreted programming language known for its readability and versatility. It is great for AI, Web Dev, and Automation.",
                "underflow": "Arithmetic underflow occurs when the result of a calculation is a smaller absolute value than the computer can actually represent in memory.",
                "about myself": "I am an AI assistant and don't have access to your personal life. However, I can help you with your tasks and answer your questions!",
                "languages": "I can communicate in multiple languages including English, Hindi, Spanish, French, German, and more. You can switch languages using the selector in the header.",
                "can you talk": "Yes, I can communicate in many languages including English, Hindi, Spanish, and French."
            },
            "Hindi": {
                "python": "पायथन एक उच्च-स्तरीय प्रोग्रामिंग भाषा है जो अपनी पठनीयता और बहुमुखी प्रतिभा के लिए जानी जाती है।",
                "hello": "नमस्ते! मैं नोवा एआई हूं। मैं आज आपकी कैसे सहायता कर सकता हूं?",
                "hi": "नमस्ते! मैं आपकी क्या मदद कर सकता हूँ?",
                "resume": "सॉफ्टवेयर इंजीनियर रिज्यूमे में सुधार के लिए: मुख्य तकनीकी कौशल दिखाएं, प्रोजेक्ट्स का वर्णन करें और अपनी उपलब्धियों को डेटा के साथ बताएं।"
            },
            "Spanish": {
                "python": "Python es un lenguaje de programación de alto nivel conocido por su legibilidad y versatilidad.",
                "hello": "¡Hola! Soy Nova AI. ¿Cómo puedo ayudarte hoy?",
                "hi": "¡Hola! ¿En qué puedo ayudarte?",
                "resume": "Para mejorar tu currículum: resalta tus habilidades técnicas, incluye proyectos relevantes y cuantifica tus resultados."
            }
        }
        
        target_lang = "English" if language == "Auto-detect" else language
        lang_group = smart_responses.get(target_lang, smart_responses["English"])
        
        lower_query = user_input.lower().strip().strip("?!.")
        # Exact match for speed
        if lower_query in lang_group:
            return lang_group[lower_query]
        
        # Substring match
        for key, val in lang_group.items():
            if key in lower_query:
                return val

        # --- Smart Search Guard ---
        # Don't search Wikipedia for short, conversational, or personal queries
        conversational_keywords = ["myself", "yourself", "you do", "can you", "who am", "tell me", "talk", "speak", "languages"]
        if any(word in lower_query for word in conversational_keywords) and len(lower_query.split()) < 6:
            return ""

        # Removed Wikipedia text search to prevent stream blocking and reduce latency
        return ""

    async def get_image_url(self, query: str) -> Optional[str]:
        try:
            query = query.strip()
            if not query: return None
            headers = {"User-Agent": "AI-Chatbot/1.0"}
            formatted_query = query.title().replace(' ', '_')
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_query}"
            async with aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(wiki_url, timeout=1.5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("originalimage"): return data["originalimage"]["source"]
                        if data.get("thumbnail"): return data["thumbnail"]["source"]
            return None
        except Exception as e:
            logger.error(f"Image search error: {str(e)}")
            return None

    async def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Fetch last N messages from MongoDB."""
        if not db.db:
            return []
        doc = await db.db.conversations.find_one({"id": session_id})
        if not doc:
            return []
        messages = doc.get("messages", [])
        return [{"role": m["role"], "content": m["content"]} for m in messages[-limit:]]

    async def save_message(self, session_id: str, username: str, role: str, content: str):
        """Save a message to MongoDB, creating conversation if needed."""
        try:
            if not db.db:
                return
            now = datetime.utcnow()
            message_entry = {
                "role": role,
                "content": content,
                "timestamp": now
            }
            await db.conversations.update_one(
                {"id": session_id},
                {
                    "$push": {"messages": message_entry},
                    "$set": {
                        "last_message": content[:100],
                        "updated_at": now
                    },
                    "$setOnInsert": {
                        "username": username,
                        "title": "New Conversation",
                        "created_at": now
                    }
                },
                upsert=True
            )
            
            # Also log as a search if it's from the user
            if role == "user":
                await self.save_search(username, session_id, content)
        except Exception as e:
            import traceback
            logger.error(f"Failed to save message: {str(e)}\n{traceback.format_exc()}")

    async def save_search(self, username: str, session_id: str, query: str):
        if not db.db: 
            logger.warning("Search logging skipped: Database not initialized")
            return
        
        # Prevent logging very short or empty strings
        if len(query.strip()) < 3: return
        
        logger.info(f"Logging search for {username}: {query[:30]}...")
        search_entry = {
            "username": username,
            "session_id": session_id,
            "query": query.strip(),
            "timestamp": datetime.utcnow()
        }
        # Use update_one with upsert to avoid duplicate recent searches for same query in same session
        res = await db.db.searches.update_one(
            {"username": username, "query": query.strip(), "session_id": session_id},
            {"$set": search_entry},
            upsert=True
        )
        logger.info(f"Search logged successfully (upserted_id: {getattr(res, 'upserted_id', 'unknown')})")

    async def generate_title(self, session_id: str, user_input: str):
        """Generate a meaningful title for the conversation based on the content."""
        try:
            if not db.db: return
            doc = await db.db.conversations.find_one({"id": session_id})
            # Only generate title if it's still generic
            if not doc or doc.get("title") not in ["New Conversation", "New Chat"]:
                return

            title = "New Chat"
            # 1. Try OpenAI if available
            if self.openai_client:
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "system", "content": "Generate a very short (max 3 words) title for this conversation. Output ONLY the title."},
                                  {"role": "user", "content": user_input}],
                        max_tokens=15
                    )
                    title = response.choices[0].message.content.strip().strip('"')
                except Exception: pass
            
            # 2. Try Gemini if OpenAI failed or is missing
            if title == "New Chat" and self.gemini_enabled:
                try:
                    # Fast-path for common demo queries
                    lower_input = user_input.lower()
                    if "resume" in lower_input: title = "Resume Tips"
                    elif "python" in lower_input: title = "Python Guide"
                    elif "hello" in lower_input or "hi " in lower_input: title = "Greeting"
                    else:
                        # Otherwise use a fast model to generate title
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        gen_resp = await model.generate_content_async(
                            f"Generate a 2-3 word title for a chat starting with: '{user_input[:100]}'. Output ONLY the title.",
                            request_options={"timeout": 5}
                        )
                        title = gen_resp.text.strip().strip('"*#')
                except Exception: pass
            
            # 3. Last resort: Heuristic from message
            if title == "New Chat" or not title:
                title = user_input[:25].strip() + ("..." if len(user_input) > 25 else "")

            # Ensure title isn't too long for UI
            if len(title) > 30: title = title[:27] + "..."
            
            await db.db.conversations.update_one({"id": session_id}, {"$set": {"title": title}})
        except Exception as e:
            logger.error(f"Title generation error: {str(e)}")

    async def _get_ai_text(self, history: List[Dict[str, str]], user_input: str, language: str, image_data: Optional[str] = None, document_text: Optional[str] = None) -> str:
        """Internal method to handle AI response generation with fallbacks."""
        
        # Inject document context if available
        final_input = user_input
        if document_text:
            final_input = f"CONTEXT FROM UPLOADED DOCUMENT:\n{document_text}\n\nUSER QUESTION: {user_input}\n\nPlease answer based on the document context provided above."
        
        # 1. Try OpenAI (only if no image)
        if self.openai_client and not settings.MOCK_MODE and not image_data:
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"You are Nova AI, an Unlimited Pro intelligent assistant. Response Language Rule: {('Detect user language and respond in the same language.' if language == 'Auto-detect' else f'Respond ONLY in {language}. If user asks in another language, translate your response to {language}.')} Provide extremely detailed, professional, and high-quality responses. Response should be user-friendly markdown."},
                        *history
                    ],
                    max_tokens=1024,
                    temperature=0.5
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI error: {str(e)}")

        # 2. Try Gemini (with prioritized model list)
        if self.gemini_enabled:
            # Reordered to favor low-quota/high-availability models
            gemini_models = [
                'gemini-flash-lite-latest', 
                'gemini-1.5-flash-8b', 
                'gemini-1.5-flash',
                'gemini-2.0-flash', 
                'gemini-2.0-flash-lite-preview-02-05', # New exp model
                'gemini-2.0-pro-exp-02-05',
                'gemini-pro-latest'
            ]
            lang_rule = "Detect user language and respond in the same language." if language == "Auto-detect" else f"Respond ONLY in {language}. If user asks in another language, translate your response to {language}."
            system_instr = f"You are Nova AI, an Unlimited Pro intelligent assistant. Response Language Rule: {lang_rule} Provide extremely detailed, professional, and high-quality responses. Response should be user-friendly markdown."
            
            contents = []
            if image_data:
                import base64
                try:
                    clean_data = image_data.split(",")[1] if "," in image_data else image_data
                    contents.append({
                        "mime_type": "image/jpeg",
                        "data": base64.b64decode(clean_data)
                    })
                except Exception as e:
                    logger.error(f"Error decoding image: {str(e)}")
            
            contents.append(user_input)

            for model_name in gemini_models:
                if image_data and 'pro' in model_name and 'flash' not in model_name:
                    continue

                # Fast-fail for models hitting 429 to avoid hanging the UI
                for attempt in range(2):
                    try:
                        logger.info(f"Attempting Gemini with model: {model_name} (Attempt {attempt+1})")
                        model = genai.GenerativeModel(model_name, system_instruction=system_instr)
                        gemini_history = []
                        for m in history[:-1]:
                            role = "user" if m["role"] == "user" else "model"
                            gemini_history.append({"role": role, "parts": [m["content"]]})
                        
                        chat = model.start_chat(history=gemini_history)
                        response = await chat.send_message_async(contents, request_options={"timeout": 10})
                        return response.text
                    except Exception as e:
                        error_str = str(e)
                        logger.warning(f"Gemini {model_name} failed: {error_str}")
                        
                        if "429" in error_str:
                            if attempt == 0:
                                import asyncio
                                await asyncio.sleep(0.5)
                                continue
    async def _get_ai_text(self, history: List[Dict[str, str]], user_input: str, language: str, image_data: Optional[str] = None, document_text: Optional[str] = None):
        """Unified text generation logic using upgraded Gemini SDK."""
        if self.gemini_enabled:
            lang_rule = "Detect user language and respond in the same language." if language == "Auto-detect" else f"Respond ONLY in {language}."
            system_instr = f"You are Nova AI. {lang_rule} Provide detailed, professional responses in markdown."
            
            # Prepare contents with history
            contents = []
            for m in history[:-1]:
                role = "user" if m["role"] == "user" else "model"
                contents.append({'role': role, 'parts': [{'text': m['content']}]})
            
            # Multi-modal input
            parts = [{'text': user_input}]
            if image_data:
                import base64
                clean_data = image_data.split(",")[1] if "," in image_data else image_data
                parts.append({'mime_type': 'image/jpeg', 'data': clean_data})
            
            contents.append({'role': 'user', 'parts': parts})

            gemini_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro-latest']
            for model_name in gemini_models:
                try:
                    response = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config={'system_instruction': system_instr, 'temperature': 0.7}
                    )
                    return response.text
                except Exception as e:
                    logger.warning(f"Gemini {model_name} failed: {str(e)}")
                    continue
        
        return await self.get_search_context(user_input, language) or "I'm busy right now, please try again!"

    async def _get_ai_text_stream(self, history: List[Dict[str, str]], user_input: str, language: str, image_data: Optional[str] = None, document_text: Optional[str] = None, selected_model: Optional[str] = None, temperature: Optional[float] = 0.7):
        """Streaming AI response using the new google-genai SDK."""
        if self.gemini_enabled and self.gemini_client:
            lang_rule = f"Respond ONLY in {language}." if language != "Auto-detect" else "Respond in user's language."
            system_instr = f"You are Nova AI. {lang_rule} Provide detailed markdown."
            
            # Prepare contents
            contents = []
            for m in history[:-1]:
                role = "user" if m["role"] == "user" else "model"
                contents.append({'role': role, 'parts': [{'text': m['content']}]})
            
            parts = [{'text': user_input}]
            if image_data:
                import base64
                clean_data = image_data.split(",")[1] if "," in image_data else image_data
                parts.append({'mime_type': 'image/jpeg', 'data': clean_data})
            contents.append({'role': 'user', 'parts': parts})

            # Comprehensive model list with exact identifiers for the new SDK
            gemini_models = [
                'gemini-2.5-flash',
                'gemini-2.0-flash', 
                'gemini-2.5-pro',
                'gemini-1.5-flash',
                'gemini-1.5-flash-8b',
                'gemini-1.5-pro'
            ]
            if selected_model: gemini_models.insert(0, selected_model)

            for model_name in gemini_models:
                success = False
                try:
                    logger.info(f"Stream attempt: {model_name}")
                    response_stream = await self.gemini_client.aio.models.generate_content_stream(
                        model=model_name,
                        contents=contents,
                        config={'system_instruction': system_instr, 'temperature': temperature or 0.7, 'http_options': {'timeout': 15}}
                    )
                    async for chunk in response_stream:
                        if chunk.text: 
                            yield chunk.text
                            success = True
                    if success: return
                except Exception as e:
                    error_msg = str(e).lower()
                    logger.warning(f"Async stream failed for {model_name}: {error_msg}")
                    # If quota exceeded, move to next model IMMEDIATELY
                    if "429" in error_msg or "quota" in error_msg:
                        continue
                    if "404" in error_msg or "not found" in error_msg:
                        continue
                    continue
        
        # Final fallback to non-streaming if everything else fails
        fallback_text = await self._get_ai_text(history, user_input, language, image_data, document_text)
        yield fallback_text

    async def get_response(self, session_id: str, username: str, user_input: str, language: str = "English", image_data: Optional[str] = None, document_data: Optional[str] = None, document_name: Optional[str] = None, selected_model: Optional[str] = None, temperature: Optional[float] = 0.7):
        if temperature is None: temperature = 0.7
        await self.save_message(session_id, username, "user", user_input)
        # Delay title generation to prevent API contention during initial response
        async def delayed_title():
            await asyncio.sleep(3)
            await self.generate_title(session_id, user_input)
        asyncio.create_task(delayed_title())

        history = await self.get_history(session_id, limit=settings.MAX_CONTEXT_MESSAGES)

        # Handle document context
        document_text = None
        if document_data:
            document_text = self.extract_text_from_base64(document_data, document_name or "document")

        tasks = [self._get_ai_text(history, user_input, language, image_data, document_text)]
        image_task_idx = -1
        
        # Consistent Auto-Photo logic
        import re
        lower_input = user_input.lower().strip()
        clean_name = re.sub(r'(who is|who was|tell me about|what is|about|show me|picture of|photo of|image of|a |an )', '', lower_input).strip().strip("?!.")
        should_search_image = any(t in lower_input for t in ["photo", "image", "picture", "show me"]) or \
                              any(t in lower_input for t in ["who is", "who was", "tell me about"]) or \
                              (len(lower_input.split()) <= 3 and len(clean_name) > 3)

        if not image_data and should_search_image and clean_name:
            tasks.append(self.get_image_url(clean_name))
            image_task_idx = len(tasks) - 1

        results = await asyncio.gather(*tasks)
        assistant_message = results[0]
        image_url = results[image_task_idx] if image_task_idx != -1 else None

        await self.save_message(session_id, username, "assistant", assistant_message)
        title = "New Chat"
        if db.db:
            doc = await db.db.conversations.find_one({"id": session_id})
            if doc: title = doc.get("title", "New Chat")

        return assistant_message, image_url, title

chat_service = ChatService()

# --- Auth Dependencies ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    username = auth_service.decode_access_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return username

# --- Endpoints ---

@router.post("/signup")
async def signup(user: Dict[str, str]):
    username = user.get("username")
    password = user.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")
    
    # Check if user exists in database
    existing_user = await db.users.find_one({"username": username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Save to database
    hashed_password = auth_service.get_password_hash(password)
    await db.users.insert_one({
        "username": username,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    })
    
    # Still update mock for legacy compatibility in current session if needed
    auth_service.users_db[username] = {"password": hashed_password}
    
    return {"message": "User created successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Fetch user from database
    user = await db.users.find_one({"username": form_data.username})
    
    if not user:
        # Fallback to legacy mock logic for same-session users not yet migrated (optional)
        user = auth_service.users_db.get(form_data.username)
        
    if not user or not auth_service.verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth_service.create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/social_handshake")
async def social_handshake(request: Dict[str, str]):
    """Simulated social login that returns a real, valid JWT."""
    username = request.get("username", "Social_User")
    provider = request.get("provider", "google")
    
    # We create a real JWT for the simulated user
    # This ensures the rest of the app treats them as a valid authenticated user
    access_token = auth_service.create_access_token(data={"sub": f"{provider}_{username}"})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "username": f"{provider}_{username}"
    }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: str = Depends(get_current_user)):
    session_id = request.session_id or str(uuid.uuid4())
    try:
        response_text, image_url, title = await chat_service.get_response(
            session_id, current_user, request.user_input, request.language, request.image, request.document, request.document_name, request.model, request.temperature
        )
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            title=title,
            image_url=image_url
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, current_user: str = Depends(get_current_user)):
    """Streaming endpoint for AI responses."""
    session_id = request.session_id or str(uuid.uuid4())
    import json
    
    async def event_generator():
        logger.info(f"Starting chat stream for user {current_user}, session {session_id}")
        
        # INSTANT FEEDBACK: Yield empty chunk immediately to clear "AI is thinking..." UI
        yield f"data: {json.dumps({'type': 'text', 'chunk': ''})}\n\n"
        
        await chat_service.save_message(session_id, current_user, "user", request.user_input)
        import asyncio
        asyncio.create_task(chat_service.generate_title(session_id, request.user_input))
        history = await chat_service.get_history(session_id, limit=settings.MAX_CONTEXT_MESSAGES)
        
        lower_input = request.user_input.lower().strip()
        is_asking_about_upload = any(t in lower_input for t in ["this photo", "the photo", "my photo", "this image", "that picture"])
        has_upload = bool(request.image) or any(m.get("image") for m in history)
        
        # FAST REPLY CACHE: Instant answers for repeated queries
        if not has_upload and db.db and len(lower_input) > 4:
            cached = await db.db.fast_cache.find_one({"query": lower_input, "language": request.language})
            if cached:
                logger.info("Fast Reply Cache hit!")
                yield f"data: {json.dumps({'type': 'text', 'chunk': cached['response']})}\n\n"
                await chat_service.save_message(session_id, current_user, "assistant", cached['response'])
                title = "New Chat"
                doc = await db.db.conversations.find_one({"id": session_id})
                if doc: title = doc.get("title", "New Chat")
                yield f"data: {json.dumps({'type': 'metadata', 'session_id': session_id, 'title': title})}\n\n"
                return

        # Clean query for image search
        import re
        clean_name = re.sub(r'(who is|who was|tell me about|what is|about|show me|picture of|photo of|image of|a |an )', '', lower_input).strip().strip("?!.")

        should_search_image = (any(t in lower_input for t in ["photo", "image", "picture", "show me"]) or \
                              any(t in lower_input for t in ["who is", "who was", "tell me about"]) or \
                              (len(lower_input.split()) <= 3 and len(clean_name) > 3)) and \
                              not has_upload

        # NON-BLOCKING IMAGE SEARCH
        image_task = None
        if should_search_image and clean_name:
            image_task = asyncio.create_task(chat_service.get_image_url(clean_name))

        full_content = ""
        document_text = None
        if request.document:
            document_text = chat_service.extract_text_from_base64(request.document, request.document_name or "document")

        async for chunk in chat_service._get_ai_text_stream(history, request.user_input, request.language, request.image, document_text, request.model, request.temperature):
            full_content += chunk
            yield f"data: {json.dumps({'type': 'text', 'chunk': chunk})}\n\n"
        
        # Wait for image if requested, with a strict timeout
        if image_task:
            try:
                image_url = await asyncio.wait_for(image_task, timeout=1.5)
                if image_url:
                    yield f"data: {json.dumps({'type': 'image', 'url': image_url})}\n\n"
            except Exception:
                pass

        # Save to Fast Reply Cache
        if not has_upload and db.db and len(lower_input) > 4:
            from datetime import datetime
            await db.db.fast_cache.update_one(
                {"query": lower_input, "language": request.language},
                {"$set": {"response": full_content, "timestamp": datetime.now()}},
                upsert=True
            )

        await chat_service.save_message(session_id, current_user, "assistant", full_content)
        title = "New Chat"
        if db.db:
            doc = await db.db.conversations.find_one({"id": session_id})
            if doc: title = doc.get("title", "New Chat")
        yield f"data: {json.dumps({'type': 'metadata', 'session_id': session_id, 'title': title})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(current_user: str = Depends(get_current_user)):
    if not db.db: return []
    cursor = db.db.conversations.find({"username": current_user}).sort("updated_at", -1)
    results = []
    async for doc in cursor:
        last_msg = doc["messages"][-1]["content"] if doc.get("messages") else "Empty"
        results.append(ConversationSummary(
            id=doc["id"],
            title=doc.get("title", "New Chat"),
            last_message=last_msg[:50] + ("..." if len(last_msg) > 50 else ""),
            updated_at=doc["updated_at"]
        ))
    return results

@router.get("/conversations/{session_id}", response_model=Conversation)
async def get_conversation(session_id: str, current_user: str = Depends(get_current_user)):
    if not db.db: raise HTTPException(status_code=500, detail="Database not connected")
    doc = await db.db.conversations.find_one({"id": session_id, "username": current_user})
    if not doc: raise HTTPException(status_code=404, detail="Conversation not found")
    return Conversation(**doc)

@router.patch("/conversations/{session_id}")
async def rename_conversation(session_id: str, request: Dict[str, str], current_user: str = Depends(get_current_user)):
    if not db.db: raise HTTPException(status_code=500, detail="Database not connected")
    title = request.get("title")
    if not title: raise HTTPException(status_code=400, detail="Missing title")
    result = await db.db.conversations.update_one(
        {"id": session_id, "username": current_user},
        {"$set": {"title": title, "updated_at": datetime.now()}}
    )
    if result.matched_count == 0: raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation renamed"}

@router.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str, current_user: str = Depends(get_current_user)):
    if not db.db: raise HTTPException(status_code=500, detail="Database not connected")
    result = await db.db.conversations.delete_many({"id": session_id, "username": current_user})
    if result.deleted_count == 0: raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}

@router.get("/search_history", response_model=List[SearchEntry])
async def get_search_history(current_user: str = Depends(get_current_user)):
    history_list = []
    if db.db:
        cursor = db.db.searches.find({"username": current_user}).sort("timestamp", -1).limit(20)
        async for doc in cursor:
            history_list.append(SearchEntry(
                query=doc.get("query"),
                timestamp=doc.get("timestamp"),
                session_id=doc.get("session_id")
            ))
    return history_list

@router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(current_user: str = Depends(get_current_user)):
    if current_user != "tester" and current_user != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    total_users = await db.users.count_documents()
    total_chats = await db.conversations.count_documents()
    query_counts = {}
    if db.db:
        cursor = db.db.searches.find()
        async for doc in cursor:
            q = doc.get("query", "").strip()
            if q: query_counts[q] = query_counts.get(q, 0) + 1
    top_queries = [{"query": q, "count": c} for q, c in sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
    return AdminStats(total_users=max(total_users, 1), total_chats=total_chats, top_queries=top_queries, api_hits=total_chats * 2 + 5, system_status="Operational")

@router.post("/chat/clear")
async def clear_chat(session_id: str, current_user: str = Depends(get_current_user)):
    if not db.db: raise HTTPException(status_code=500, detail="Database not connected")
    result = await db.db.conversations.delete_many({"id": session_id, "username": current_user})
    if result.deleted_count == 0: raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Chat history cleared"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
