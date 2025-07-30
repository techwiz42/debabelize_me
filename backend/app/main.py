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
import traceback

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

# Create debabelizer configuration with API keys from settings
def create_debabelizer_config():
    """Create DebabelizerConfig with API keys for all supported STT and TTS providers"""
    config_dict = {}
    
    # STT Providers
    if hasattr(settings, 'deepgram_api_key') and settings.deepgram_api_key:
        config_dict['deepgram'] = {'api_key': settings.deepgram_api_key}
    
    if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
        config_dict['openai'] = {'api_key': settings.openai_api_key}
    
    if hasattr(settings, 'azure_speech_key') and settings.azure_speech_key:
        config_dict['azure'] = {'api_key': settings.azure_speech_key}
        if hasattr(settings, 'azure_speech_region') and settings.azure_speech_region:
            config_dict['azure']['region'] = settings.azure_speech_region
    
    if hasattr(settings, 'google_application_credentials') and settings.google_application_credentials:
        config_dict['google'] = {'credentials_path': settings.google_application_credentials}
    
    if hasattr(settings, 'soniox_api_key') and settings.soniox_api_key:
        config_dict['soniox'] = {'api_key': settings.soniox_api_key}
    
    # TTS Providers  
    if hasattr(settings, 'elevenlabs_api_key') and settings.elevenlabs_api_key:
        if 'elevenlabs' not in config_dict:
            config_dict['elevenlabs'] = {}
        config_dict['elevenlabs']['api_key'] = settings.elevenlabs_api_key
    
    # Set preferences based on environment settings
    config_dict['preferences'] = {
        'optimize_for': getattr(settings, 'debabelizer_optimize_for', 'balanced')
    }
    
    return DebabelizerConfig(config_dict)

debabelizer_config = create_debabelizer_config()

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
    """
    try:
        global tts_processor, stt_processor
        
        if not tts_processor or not stt_processor:
            return text
        
        # Convert text to speech
        tts_result = await tts_processor.synthesize(text=text)
        
        # Convert audio back to text
        stt_result = await stt_processor.transcribe_audio(
            audio_data=tts_result.audio_data,
            audio_format=settings.elevenlabs_output_format.split('_')[0]
        )
        
        return stt_result.text
        
    except Exception as e:
        traceback.print_exc()
        print(f"Debabelizer error: {e}")
        return text

@app.on_event("startup")
async def startup_event():
    global stt_processor, tts_processor
    try:
        print(f"Starting initialization with STT provider: {settings.debabelizer_stt_provider}, TTS provider: {settings.debabelizer_tts_provider}")
        print(f"Available API keys: Deepgram={bool(settings.deepgram_api_key)}, ElevenLabs={bool(settings.elevenlabs_api_key)}, OpenAI={bool(settings.openai_api_key)}")
        
        # Create VoiceProcessor instances with explicit provider settings
        if settings.debabelizer_stt_provider and (
            (settings.debabelizer_stt_provider == 'deepgram' and settings.deepgram_api_key) or
            (settings.debabelizer_stt_provider == 'openai' and settings.openai_api_key) or
            (settings.debabelizer_stt_provider == 'azure' and settings.azure_speech_key) or
            (settings.debabelizer_stt_provider == 'soniox' and settings.soniox_api_key) or
            (settings.debabelizer_stt_provider == 'whisper') or  # Whisper doesn't need API key
            (settings.debabelizer_stt_provider == 'google' and settings.google_application_credentials)
        ):
            stt_processor = VoiceProcessor(
                stt_provider=settings.debabelizer_stt_provider,
                config=debabelizer_config
            )
            print(f"STT processor created with {settings.debabelizer_stt_provider}")
        else:
            print(f"STT provider {settings.debabelizer_stt_provider} not configured or missing API key")
        
        if settings.debabelizer_tts_provider and (
            (settings.debabelizer_tts_provider == 'elevenlabs' and settings.elevenlabs_api_key) or
            (settings.debabelizer_tts_provider == 'openai' and settings.openai_api_key) or
            (settings.debabelizer_tts_provider == 'azure' and settings.azure_speech_key) or
            (settings.debabelizer_tts_provider == 'google' and settings.google_application_credentials)
        ):
            tts_processor = VoiceProcessor(
                tts_provider=settings.debabelizer_tts_provider,
                config=debabelizer_config
            )
            print(f"TTS processor created with {settings.debabelizer_tts_provider}")
        else:
            print(f"TTS provider {settings.debabelizer_tts_provider} not configured or missing API key")
        
        print(f"Initialization complete. STT: {bool(stt_processor)}, TTS: {bool(tts_processor)}")
    except Exception as e:
        print(f"Error initializing processors: {e}")
        traceback.print_exc()

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
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using debabelizer TTS."""
    try:
        if not tts_processor:
            raise HTTPException(status_code=500, detail="TTS processor not initialized")
        
        # Use appropriate default voice based on provider
        default_voice = "alloy"  # OpenAI voice
        if settings.debabelizer_tts_provider == "elevenlabs":
            default_voice = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs Rachel voice ID
        elif settings.debabelizer_tts_provider == "azure":
            default_voice = "en-US-JennyNeural"  # Azure voice
        elif settings.debabelizer_tts_provider == "google":
            default_voice = "en-US-Standard-A"  # Google voice
        
        result = await tts_processor.synthesize(
            request.text,
            voice=request.voice or default_voice,
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
        
        # Start streaming transcription session with minimal Deepgram parameters
        try:
            print(f"Attempting to start Deepgram streaming session...")
            session_id = await stt_processor.start_streaming_transcription(
                audio_format="wav",
                sample_rate=16000
            )
            print(f"Deepgram streaming session started successfully: {session_id}")
        except Exception as e:
            print(f"Detailed Deepgram streaming error: {e}")
            print(f"Error type: {type(e)}")
            traceback.print_exc()
            await websocket.send_json({"error": f"Failed to start streaming: {str(e)}"})
            return
        
        # Handle incoming audio and send back results
        while True:
            data = await websocket.receive_bytes()
            await stt_processor.stream_audio(session_id, data)
            
            # Get streaming results
            async for result in stt_processor.get_streaming_results(session_id):
                await websocket.send_json({
                    "text": result.text,
                    "is_final": result.is_final,
                    "language": result.language_detected if hasattr(result, 'language_detected') else None
                })
        
    except WebSocketDisconnect:
        if 'session_id' in locals():
            await stt_processor.stop_streaming_transcription(session_id)
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
                'af': 'Afrikaans',
                'sq': 'Albanian',
                'ar': 'Arabic',
                'az': 'Azerbaijani',
                'eu': 'Basque',
                'be': 'Belarusian',
                'bn': 'Bengali',
                'bs': 'Bosnian',
                'bg': 'Bulgarian',
                'ca': 'Catalan',
                'zh': 'Chinese',
                'hr': 'Croatian',
                'cs': 'Czech',
                'da': 'Danish',
                'nl': 'Dutch',
                'en': 'English',
                'et': 'Estonian',
                'fi': 'Finnish',
                'fr': 'French',
                'gl': 'Galician',
                'de': 'German',
                'el': 'Greek',
                'gu': 'Gujarati',
                'he': 'Hebrew',
                'hi': 'Hindi',
                'hu': 'Hungarian',
                'id': 'Indonesian',
                'it': 'Italian',
                'ja': 'Japanese',
                'kn': 'Kannada',
                'kk': 'Kazakh',
                'ko': 'Korean',
                'lv': 'Latvian',
                'lt': 'Lithuanian',
                'mk': 'Macedonian',
                'ms': 'Malay',
                'ml': 'Malayalam',
                'mr': 'Marathi',
                'no': 'Norwegian',
                'fa': 'Persian',
                'pl': 'Polish',
                'pt': 'Portuguese',
                'pa': 'Punjabi',
                'ro': 'Romanian',
                'ru': 'Russian',
                'sr': 'Serbian',
                'sk': 'Slovak',
                'sl': 'Slovenian',
                'es': 'Spanish',
                'sw': 'Swahili',
                'sv': 'Swedish',
                'tl': 'Tagalog',
                'ta': 'Tamil',
                'te': 'Telugu',
                'th': 'Thai',
                'tr': 'Turkish',
                'uk': 'Ukrainian',
                'ur': 'Urdu',
                'vi': 'Vietnamese',
                'cy': 'Welsh'
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
            # Re-create messages with system prompt for language consistency
            final_messages = [
                {"role": "system", "content": system_prompt},
                *conversation_history[1:]  # Skip the old system message if any
            ]
            final_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=final_messages,
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
                    'af': 'Afrikaans',
                    'sq': 'Albanian',
                    'ar': 'Arabic',
                    'az': 'Azerbaijani',
                    'eu': 'Basque',
                    'be': 'Belarusian',
                    'bn': 'Bengali',
                    'bs': 'Bosnian',
                    'bg': 'Bulgarian',
                    'ca': 'Catalan',
                    'zh': 'Chinese',
                    'hr': 'Croatian',
                    'cs': 'Czech',
                    'da': 'Danish',
                    'nl': 'Dutch',
                    'en': 'English',
                    'et': 'Estonian',
                    'fi': 'Finnish',
                    'fr': 'French',
                    'gl': 'Galician',
                    'de': 'German',
                    'el': 'Greek',
                    'gu': 'Gujarati',
                    'he': 'Hebrew',
                    'hi': 'Hindi',
                    'hu': 'Hungarian',
                    'id': 'Indonesian',
                    'it': 'Italian',
                    'ja': 'Japanese',
                    'kn': 'Kannada',
                    'kk': 'Kazakh',
                    'ko': 'Korean',
                    'lv': 'Latvian',
                    'lt': 'Lithuanian',
                    'mk': 'Macedonian',
                    'ms': 'Malay',
                    'ml': 'Malayalam',
                    'mr': 'Marathi',
                    'no': 'Norwegian',
                    'fa': 'Persian',
                    'pl': 'Polish',
                    'pt': 'Portuguese',
                    'pa': 'Punjabi',
                    'ro': 'Romanian',
                    'ru': 'Russian',
                    'sr': 'Serbian',
                    'sk': 'Slovak',
                    'sl': 'Slovenian',
                    'es': 'Spanish',
                    'sw': 'Swahili',
                    'tl': 'Tagalog',
                    'ta': 'Tamil',
                    'te': 'Telugu',
                    'th': 'Thai',
                    'tr': 'Turkish',
                    'uk': 'Ukrainian',
                    'ur': 'Urdu',
                    'vi': 'Vietnamese',
                    'cy': 'Welsh'
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
                # Re-create messages with system prompt for language consistency
                final_messages = [
                    {"role": "system", "content": system_prompt},
                    *conversation_history[1:]  # Skip the old system message if any
                ]
                final_response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=final_messages,
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
