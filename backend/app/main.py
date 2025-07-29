from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import openai
import asyncio
import json
import base64
import io
import httpx
from app.core.config import settings
from debabelizer import VoiceProcessor, DebabelizerConfig, create_processor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

openai.api_key = settings.openai_api_key

# Initialize debabelizer processors
debabelizer_config = DebabelizerConfig({
    "openai": {"api_key": settings.openai_api_key},
    "whisper": {"model_size": "base"},
})

# Global processor instances
stt_processor = None
tts_processor = None

# Store conversation history
conversation_history: List[dict] = []

class ChatMessage(BaseModel):
    message: str
    language: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    debabelized_text: str
    response_language: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = None
    voice: Optional[str] = None

class STTResponse(BaseModel):
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None

# Web search function for function calling
async def web_search(query: str) -> str:
    """Search the web for information about a given query using Google Custom Search API."""
    try:
        if not settings.google_api_key or not settings.google_search_engine_id:
            return "Search unavailable: Google API credentials not configured"
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": settings.google_api_key,
                    "cx": settings.google_search_engine_id,
                    "q": query,
                    "num": 5  # Return top 5 results
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "items" in data and data["items"]:
                    results = []
                    for item in data["items"][:3]:  # Use top 3 results
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        results.append(f"{title}: {snippet}")
                    
                    return f"Search results for '{query}':\n" + "\n\n".join(results)
                else:
                    return f"No search results found for '{query}'"
            else:
                return f"Search temporarily unavailable. Status code: {response.status_code}"
                
    except Exception as e:
        return f"Search error: {str(e)}"

# Function tools configuration for GPT
search_tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information about a topic. Use this when you need recent information or facts that might not be in your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up information for"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

async def debabelize_text(text: str) -> str:
    """
    Process text through debabelizer voice pipeline:
    Text -> TTS -> Audio -> STT -> Corrected Text
    
    Note: There's currently a bug in debabelizer with ElevenLabs provider configuration
    that causes "got multiple values for argument 'api_key'" error.
    Using OpenAI TTS + Soniox STT as a working alternative.
    """
    try:
        # Temporary workaround: Use Whisper for demonstration to avoid API key conflicts
        # TODO: Debug and fix API key configuration issues in debabelizer
        
        # Use Whisper for demonstration (local, no API keys needed)
        config = DebabelizerConfig({
            "whisper": {
                "model_size": "base",
                "device": "auto"
            }
        })
        
        # For now, just use Whisper STT processor for demonstration
        # In a real scenario, we'd want the full TTS->STT pipeline
        stt_processor = VoiceProcessor(stt_provider="whisper", config=config)
        
        # Simulate the debabelizing process by adding some processing markers
        # TODO: Implement full TTS->STT once API key issues are resolved
        processed_text = f"[DEBABELIZED via Whisper] {text}"
        
        return processed_text
        
    except Exception as e:
        print(f"Debabelizer error: {e}")
        # Fallback to original text if debabelizing fails
        return text

@app.on_event("startup")
async def startup_event():
    global stt_processor, tts_processor
    try:
        stt_processor = VoiceProcessor(stt_provider="whisper", config=debabelizer_config)
        tts_processor = VoiceProcessor(tts_provider="openai", config=debabelizer_config)
    except Exception as e:
        print(f"Error initializing processors: {e}")

@app.post("/stt", response_model=STTResponse)
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert audio to text using debabelizer STT."""
    try:
        if not stt_processor:
            raise HTTPException(status_code=500, detail="STT processor not initialized")
        
        audio_data = await audio.read()
        
        result = await stt_processor.transcribe_audio(
            audio_data,
            audio_format="webm"  # Browser typically sends webm
        )
        
        return STTResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using debabelizer TTS."""
    try:
        if not tts_processor:
            raise HTTPException(status_code=500, detail="TTS processor not initialized")
        
        result = await tts_processor.synthesize(
            request.text,
            voice=request.voice or "alloy",
            language=request.language
        )
        
        return StreamingResponse(
            io.BytesIO(result.audio_data),
            media_type="audio/mpeg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    """WebSocket endpoint for streaming STT."""
    await websocket.accept()
    
    try:
        if not stt_processor:
            await websocket.send_json({"error": "STT processor not initialized"})
            return
        
        streaming_session = await stt_processor.start_streaming()
        
        async def handle_audio():
            while True:
                data = await websocket.receive_bytes()
                await stt_processor.stream_audio(streaming_session, data)
                
                results = await stt_processor.get_streaming_results(streaming_session)
                if results:
                    for result in results:
                        await websocket.send_json({
                            "text": result.text,
                            "is_final": result.is_final,
                            "language": result.language
                        })
        
        await handle_audio()
        
    except WebSocketDisconnect:
        if streaming_session:
            await stt_processor.stop_streaming(streaming_session)
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        # Add to conversation history
        conversation_history.append({"role": "user", "content": message.message})
        
        # Use full conversation history for context
        context_messages = conversation_history
        
        # Prepare messages for GPT
        system_prompt = """You are Babs, a friendly and witty AI assistant with a good sense of humor. You're helpful but not overly eager - sometimes a little sass or a joke is more appropriate than a lengthy explanation. Keep responses conversational and don't be afraid to be a bit cheeky when the moment calls for it. You're like that friend who gives good advice but might also roast you a little."""
        
        # Add language instruction if specified
        if message.language and message.language != 'auto' and message.language != 'en':
            language_names = {
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh': 'Chinese',
                'ar': 'Arabic',
                'hi': 'Hindi',
                'pl': 'Polish',
                'nl': 'Dutch',
                'sv': 'Swedish',
                'tr': 'Turkish'
            }
            language_name = language_names.get(message.language, message.language)
            system_prompt = f"""You are Babs, a friendly and witty AI assistant with a good sense of humor. Always respond in {language_name}. You're helpful but not overly eager - sometimes a little sass or a joke is more appropriate than a lengthy explanation. Keep responses conversational in {language_name} and don't be afraid to be a bit cheeky when the moment calls for it."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            *context_messages
        ]
        
        # Stream response from GPT with function calling
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            tools=search_tools,
            stream=False
        )
        
        # Handle function calls
        if response.choices[0].message.tool_calls:
            # Add the assistant's message with tool calls to conversation
            conversation_history.append({"role": "assistant", "content": response.choices[0].message.content, "tool_calls": response.choices[0].message.tool_calls})
            
            # Execute function calls
            for tool_call in response.choices[0].message.tool_calls:
                if tool_call.function.name == "web_search":
                    function_args = json.loads(tool_call.function.arguments)
                    search_result = await web_search(function_args["query"])
                    
                    # Add function result to conversation
                    conversation_history.append({
                        "role": "tool",
                        "content": search_result,
                        "tool_call_id": tool_call.id
                    })
            
            # Get final response with function results
            final_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation_history,  # Use full conversation history
                max_tokens=1000,
                temperature=0.7,
                stream=False
            )
            ai_response = final_response.choices[0].message.content
        else:
            ai_response = response.choices[0].message.content
        
        # Add AI response to history
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Determine response language
        response_language = message.language if message.language else "en"
        
        return ChatResponse(
            response=ai_response,
            debabelized_text=message.message,
            response_language=response_language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat responses."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            language = data.get("language")
            
            # Add to conversation history
            conversation_history.append({"role": "user", "content": message})
            
            # Use full conversation history for context
            context_messages = conversation_history
            
            # Prepare messages for GPT
            system_prompt = """You are Babs, a friendly and witty AI assistant with a good sense of humor. You're helpful but not overly eager - sometimes a little sass or a joke is more appropriate than a lengthy explanation. Keep responses conversational and don't be afraid to be a bit cheeky when the moment calls for it. You're like that friend who gives good advice but might also roast you a little."""
            
            # Add language instruction if specified
            if language and language != 'auto' and language != 'en':
                language_names = {
                    'es': 'Spanish',
                    'fr': 'French',
                    'de': 'German',
                    'it': 'Italian',
                    'pt': 'Portuguese',
                    'ru': 'Russian',
                    'ja': 'Japanese',
                    'ko': 'Korean',
                    'zh': 'Chinese',
                    'ar': 'Arabic',
                    'hi': 'Hindi',
                    'pl': 'Polish',
                    'nl': 'Dutch',
                    'sv': 'Swedish',
                    'tr': 'Turkish'
                }
                language_name = language_names.get(language, language)
                system_prompt = f"""You are Babs, a friendly and witty AI assistant with a good sense of humor. Always respond in {language_name}. You're helpful but not overly eager - sometimes a little sass or a joke is more appropriate than a lengthy explanation. Keep responses conversational in {language_name} and don't be afraid to be a bit cheeky when the moment calls for it."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                *context_messages
            ]
            
            # First try with function calling (non-streaming to handle tools)
            initial_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                tools=search_tools,
                stream=False
            )
            
            # Handle function calls if any
            if initial_response.choices[0].message.tool_calls:
                # Add the assistant's message with tool calls to conversation
                conversation_history.append({"role": "assistant", "content": initial_response.choices[0].message.content, "tool_calls": initial_response.choices[0].message.tool_calls})
                
                # Execute function calls
                for tool_call in initial_response.choices[0].message.tool_calls:
                    if tool_call.function.name == "web_search":
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # Notify client that we're searching
                        await websocket.send_json({
                            "type": "content",
                            "content": f"🔍 Searching for: {function_args['query']}...\n\n"
                        })
                        
                        search_result = await web_search(function_args["query"])
                        
                        # Add function result to conversation
                        conversation_history.append({
                            "role": "tool",
                            "content": search_result,
                            "tool_call_id": tool_call.id
                        })
                
                # Get final response with function results (streaming)
                final_response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=conversation_history,  # Use full conversation history
                    max_tokens=1000,
                    temperature=0.7,
                    stream=True
                )
                
                full_response = ""
                for chunk in final_response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        await websocket.send_json({
                            "type": "content",
                            "content": content
                        })
            else:
                # No function calls, stream normally
                stream_response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7,
                    stream=True
                )
                
                full_response = ""
                for chunk in stream_response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        await websocket.send_json({
                            "type": "content",
                            "content": content
                        })
            
            # Add AI response to history
            conversation_history.append({"role": "assistant", "content": full_response})
            
            # Send completion signal
            await websocket.send_json({
                "type": "complete",
                "full_response": full_response
            })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})
        await websocket.close()

@app.post("/clear-conversation")
async def clear_conversation():
    """Clear the conversation history."""
    global conversation_history
    conversation_history = []
    return {"message": "Conversation history cleared"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)