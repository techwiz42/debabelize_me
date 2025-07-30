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

# Store conversation history per session
from typing import Dict
import uuid
from datetime import datetime, timedelta

session_conversations: Dict[str, Dict[str, any]] = {}

# Session cleanup settings
SESSION_TIMEOUT_HOURS = 24
CLEANUP_INTERVAL_HOURS = 1
last_cleanup = datetime.now()

class ChatMessage(BaseModel):
    message: str
    language: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    debabelized_text: str
    response_language: Optional[str] = None
    session_id: str

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

def cleanup_old_sessions():
    """Remove sessions that haven't been accessed in SESSION_TIMEOUT_HOURS."""
    global last_cleanup
    current_time = datetime.now()
    
    # Only run cleanup if enough time has passed
    if current_time - last_cleanup < timedelta(hours=CLEANUP_INTERVAL_HOURS):
        return
    
    last_cleanup = current_time
    timeout_threshold = current_time - timedelta(hours=SESSION_TIMEOUT_HOURS)
    
    sessions_to_remove = []
    for session_id, session_data in session_conversations.items():
        if session_data.get('last_accessed', current_time) < timeout_threshold:
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        del session_conversations[session_id]
    
    if sessions_to_remove:
        print(f"Cleaned up {len(sessions_to_remove)} old sessions")

def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create a new one."""
    cleanup_old_sessions()
    
    if not session_id or session_id not in session_conversations:
        session_id = str(uuid.uuid4())
        session_conversations[session_id] = {
            'conversation_history': [],
            'created_at': datetime.now(),
            'last_accessed': datetime.now()
        }
        print(f"Created new session: {session_id}")
    else:
        # Update last accessed time
        session_conversations[session_id]['last_accessed'] = datetime.now()
    
    return session_id

def get_session_conversation_history(session_id: str) -> List[dict]:
    """Get conversation history for a specific session."""
    if session_id in session_conversations:
        return session_conversations[session_id]['conversation_history']
    return []

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

# Audio buffering configuration for fake streaming approach
AUDIO_BUFFER_CONFIG = {
    "min_buffer_size": 16000,      # ~1 second at 16kHz PCM (2 bytes per sample) - more reliable transcription
    "max_buffer_size": 32000,      # ~2 seconds at 16kHz PCM - prevent memory overflow
    "silence_timeout": 0.5,        # 500ms timeout for processing buffer - balance between accumulation and responsiveness
    "sample_rate": 16000,          # PCM sample rate from frontend
    "channels": 1                  # Mono audio
}

# Track active buffering sessions
buffering_sessions = {}

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    """WebSocket endpoint for buffered STT using fake streaming approach."""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    # Initialize buffering session
    buffering_sessions[session_id] = {
        "audio_buffer": bytearray(),
        "last_audio_time": None,
        "last_process_time": None
    }
    
    try:
        if not stt_processor:
            await websocket.send_json({"error": "STT processor not initialized"})
            return
        
        print(f"Started buffered STT session: {session_id}")
        
        # Handle incoming audio and send back results
        while True:
            try:
                # Increase timeout to prevent premature disconnections - frontend sends keepalive
                data = await asyncio.wait_for(websocket.receive_bytes(), timeout=60.0)
                current_time = asyncio.get_event_loop().time()
                
                if len(data) == 0:
                    # Keepalive ping - continue silently
                    continue
                
                print(f"Received audio data: {len(data)} bytes")
                
                # Add to buffer
                session = buffering_sessions[session_id]
                session["audio_buffer"].extend(data)
                session["last_audio_time"] = current_time
                
                buffer_size = len(session["audio_buffer"])
                time_since_last_process = (
                    current_time - session["last_process_time"] 
                    if session["last_process_time"] else float('inf')
                )
                time_since_last_audio = (
                    current_time - session["last_audio_time"]
                    if session["last_audio_time"] else 0
                )
                
                # Process more aggressively for lower latency
                should_process = (
                    buffer_size >= AUDIO_BUFFER_CONFIG["max_buffer_size"] or  # Prevent memory overflow
                    (buffer_size >= AUDIO_BUFFER_CONFIG["min_buffer_size"] and 
                     time_since_last_process >= AUDIO_BUFFER_CONFIG["silence_timeout"])  # Use configured timeout
                )
                
                print(f"Buffer status: size={buffer_size}, time_since_process={time_since_last_process:.2f}s, should_process={should_process}")
                
                if should_process and buffer_size > 0:
                    # Extract buffered audio
                    buffered_audio = bytes(session["audio_buffer"])
                    
                    # Clear the buffer and update process time
                    session["audio_buffer"] = bytearray()
                    session["last_process_time"] = current_time
                    
                    print(f"Processing {len(buffered_audio)} bytes of buffered audio")
                    
                    # Debug: Check if audio is just silence
                    import struct
                    try:
                        # First check raw byte data
                        print(f"Raw audio data - Length: {len(buffered_audio)}, First 20 bytes: {buffered_audio[:20]}")
                        print(f"Raw audio data - As hex: {buffered_audio[:20].hex()}")
                        
                        # Check if length is even (required for 16-bit data)
                        if len(buffered_audio) % 2 != 0:
                            print(f"WARNING: Audio data length {len(buffered_audio)} is not divisible by 2 - padding with zero")
                            buffered_audio += b'\x00'
                        
                        # Unpack as 16-bit signed integers
                        samples = struct.unpack(f'{len(buffered_audio)//2}h', buffered_audio)
                        max_amplitude = max(abs(s) for s in samples) if samples else 0
                        avg_amplitude = sum(abs(s) for s in samples) / len(samples) if samples else 0
                        print(f"Audio analysis - Max amplitude: {max_amplitude}, Avg amplitude: {avg_amplitude:.2f}, Samples: {len(samples)}")
                        
                        # Check for silence
                        non_zero_samples = sum(1 for s in samples if s != 0)
                        print(f"Non-zero samples: {non_zero_samples}/{len(samples)} ({non_zero_samples/len(samples)*100:.1f}%)")
                        
                    except Exception as e:
                        print(f"Error analyzing audio: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    try:
                        # Process raw PCM data directly - faster than WAV conversion
                        result = await stt_processor.transcribe_chunk(
                            audio_data=buffered_audio,
                            audio_format="pcm",  # Raw PCM for efficiency
                            sample_rate=AUDIO_BUFFER_CONFIG["sample_rate"],
                            channels=AUDIO_BUFFER_CONFIG["channels"]
                        )
                        
                        print(f"Transcription result: '{result.text}' (confidence: {result.confidence})")
                        
                        # Send result to frontend if not empty
                        if result.text.strip():
                            response_data = {
                                "text": result.text,
                                "is_final": True,  # Chunk results are always final
                                "language": result.language_detected,
                                "confidence": result.confidence
                            }
                            print(f"Sending WebSocket response: {response_data}")
                            await websocket.send_json(response_data)
                            
                            # Log session state after sending
                            print(f"Session state after transcription - buffer size: {len(session['audio_buffer'])}, last_process_time: {session['last_process_time']}")
                        else:
                            print("Transcription result was empty, not sending")
                            
                    except Exception as transcription_error:
                        print(f"Error transcribing buffered audio: {transcription_error}")
                        traceback.print_exc()
                        # Don't break the loop, continue processing new audio
                        
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.01)
                
            except asyncio.TimeoutError:
                print(f"WebSocket timeout - no data received for 60s, session {session_id}")
                break
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for session {session_id}")
                break
            except Exception as loop_error:
                print(f"Error in audio processing loop: {loop_error}")
                traceback.print_exc()
                break
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        # Clean up buffering session
        if session_id in buffering_sessions:
            # Process any remaining audio in buffer before cleanup
            session = buffering_sessions[session_id]
            if len(session["audio_buffer"]) > 0:
                try:
                    print(f"Processing final {len(session['audio_buffer'])} bytes before cleanup")
                    final_audio = bytes(session["audio_buffer"])
                    result = await stt_processor.transcribe_chunk(
                        audio_data=final_audio,
                        audio_format="pcm",
                        sample_rate=AUDIO_BUFFER_CONFIG["sample_rate"],
                        channels=AUDIO_BUFFER_CONFIG["channels"]
                    )
                    if result.text.strip():
                        response_data = {
                            "text": result.text,
                            "is_final": True,
                            "language": result.language_detected,
                            "confidence": result.confidence
                        }
                        await websocket.send_json(response_data)
                except Exception as final_error:
                    print(f"Error processing final audio buffer: {final_error}")
                    
            del buffering_sessions[session_id]
            print(f"Cleaned up buffering session: {session_id}")
            
        try:
            await websocket.close()
        except:
            pass

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        # Get or create session
        session_id = get_or_create_session(message.session_id)
        conversation_history = get_session_conversation_history(session_id)
        
        # Add to session-specific conversation history
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
            response_language=response_language,
            session_id=session_id
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
            session_id_input = data.get("session_id")
            
            # Get or create session
            session_id = get_or_create_session(session_id_input)
            conversation_history = get_session_conversation_history(session_id)
            
            # Add to session-specific conversation history
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
                            "content": content,
                            "session_id": session_id
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
                            "content": content,
                            "session_id": session_id
                        })
            
            # Add AI response to history
            conversation_history.append({"role": "assistant", "content": full_response})
            
            # Send completion signal
            await websocket.send_json({
                "type": "complete",
                "full_response": full_response,
                "session_id": session_id
            })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})
        await websocket.close()

class ClearConversationRequest(BaseModel):
    session_id: Optional[str] = None

@app.post("/clear-conversation")
async def clear_conversation(request: ClearConversationRequest):
    """Clear the conversation history for a specific session or all sessions."""
    if request.session_id:
        # Clear specific session
        if request.session_id in session_conversations:
            session_conversations[request.session_id]['conversation_history'] = []
            return {"message": f"Conversation history cleared for session {request.session_id}"}
        else:
            return {"message": "Session not found"}
    else:
        # Clear all sessions (backward compatibility)
        session_conversations.clear()
        return {"message": "All conversation histories cleared"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/debug/stt")
async def debug_stt():
    """Debug endpoint to check STT configuration and test chunk transcription"""
    debug_info = {
        "stt_processor_initialized": bool(stt_processor),
        "stt_provider": settings.debabelizer_stt_provider,
        "api_key_present": bool(settings.deepgram_api_key),
        "api_key_preview": settings.deepgram_api_key[:10] + "..." if settings.deepgram_api_key else None,
        "buffering_approach": "fake_streaming",
        "active_buffering_sessions": len(buffering_sessions),
        "buffer_config": AUDIO_BUFFER_CONFIG
    }
    
    if stt_processor:
        try:
            # Try to get some info from the processor
            debug_info["processor_type"] = type(stt_processor).__name__
            debug_info["processor_provider"] = getattr(stt_processor, 'stt_provider', 'unknown')
            
            # Try a simple test - test chunk transcription with silence
            try:
                print("Attempting to test chunk transcription with test audio...")
                # Create 1 second of silence as test audio (WebM format simulation)
                test_audio = b'\x00' * 48000  # 1 second of silence at 48kHz 16-bit
                
                result = await stt_processor.transcribe_chunk(
                    audio_data=test_audio,
                    audio_format="webm",
                    sample_rate=48000,
                    channels=1
                )
                debug_info["test_chunk_transcription"] = True
                debug_info["test_result_text"] = result.text
                debug_info["test_result_confidence"] = result.confidence
                debug_info["test_result_language"] = result.language_detected
                
            except Exception as e:
                debug_info["test_chunk_error"] = str(e)
                debug_info["test_chunk_error_type"] = type(e).__name__
                import traceback
                debug_info["test_chunk_traceback"] = traceback.format_exc()
                
        except Exception as e:
            debug_info["processor_error"] = str(e)
    
    return debug_info

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    print("Shutting down - cleaning up active buffering sessions...")
    
    if buffering_sessions:
        print(f"Cleaning up {len(buffering_sessions)} buffering sessions")
        buffering_sessions.clear()
    
    print("Shutdown cleanup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
