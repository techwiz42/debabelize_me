from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io
from app.core.config import settings
from app.models.schemas import (
    ChatMessage, ChatResponse, TTSRequest, STTResponse, ClearConversationRequest
)
from app.services.voice_service import voice_service
from app.services.chat_service import chat_service
from app.services.session_service import session_service
from app.utils.audio_processing import AUDIO_BUFFER_CONFIG
from app.websockets.stt_handler import handle_stt_websocket
from app.middleware.security import SecurityMiddleware, RequestSizeLimit
from app.core.security_config import security_settings
from app.routes.auth import router as auth_router, get_current_user
from app.database.database import Database
from app.services.auth_service import auth_service
from app.utils.word_counter import count_words
from app.models.auth import UserResponse

app = FastAPI(title="Debabelizer API", description="Universal Voice Processing API")

# Include authentication routes
app.include_router(auth_router)

# Add security middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestSizeLimit, max_size=10 * 1024 * 1024)  # 10MB limit

app.add_middleware(
    CORSMiddleware,
    allow_origins=security_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize voice processors and database on startup"""
    # Initialize database
    await Database.initialize()
    
    # Initialize voice processors
    await voice_service.initialize_processors()
    
    # Clean up expired tokens and sessions
    await auth_service.cleanup_expired_data()

@app.post("/stt", response_model=STTResponse)
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert audio to text using debabelizer STT."""
    try:
        if not voice_service.stt_processor:
            raise HTTPException(status_code=500, detail="STT processor not initialized")
        
        audio_data = await audio.read()
        
        result = await voice_service.stt_processor.transcribe_audio(
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
async def text_to_speech(request: TTSRequest, current_user: UserResponse = Depends(get_current_user)):
    """Convert text to speech using debabelizer TTS."""
    try:
        print(f"TTS request - User authenticated: {current_user is not None}, Text: '{request.text[:50]}...'")
        
        if not voice_service.tts_processor:
            print("ERROR: TTS processor not initialized")
            raise HTTPException(status_code=500, detail="TTS processor not initialized")
        
        # Count words for usage tracking
        word_count = count_words(request.text)
        
        # Track usage if user is authenticated
        if current_user:
            await Database.increment_usage_stats(
                user_id=current_user.id,
                tts_words=word_count
            )
        
        result = await voice_service.tts_processor.synthesize(
            request.text,
            voice=request.voice or voice_service.get_default_voice(),
            language=request.language
        )
        
        print(f"TTS synthesis successful, returning {len(result.audio_data)} bytes")
        
        return StreamingResponse(
            io.BytesIO(result.audio_data),
            media_type="audio/mpeg"
        )
    except Exception as e:
        print(f"TTS ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    """WebSocket endpoint for buffered STT using fake streaming approach."""
    await handle_stt_websocket(websocket)

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process chat message and return response"""
    try:
        return await chat_service.process_chat_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat responses."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            await chat_service.process_streaming_chat(websocket, data)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})
        await websocket.close()

@app.post("/clear-conversation")
async def clear_conversation(request: ClearConversationRequest):
    """Clear the conversation history for a specific session or all sessions."""
    return session_service.clear_session_conversation(request.session_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/debug/stt")
async def debug_stt():
    """Debug endpoint to check STT configuration and test chunk transcription"""
    debug_info = {
        "stt_processor_initialized": bool(voice_service.stt_processor),
        "stt_provider": settings.debabelizer_stt_provider,
        "api_key_present": bool(settings.deepgram_api_key),
        "api_key_preview": settings.deepgram_api_key[:10] + "..." if settings.deepgram_api_key else None,
        "streaming_approach": "true_websocket_streaming",
        "streaming_provider": "deepgram"
    }
    
    if voice_service.stt_processor:
        try:
            # Try to get some info from the processor
            debug_info["processor_type"] = type(voice_service.stt_processor).__name__
            debug_info["processor_provider"] = getattr(voice_service.stt_processor, 'stt_provider', 'unknown')
            
            # Try a simple test - test transcription with silence
            try:
                print("Attempting to test transcription with test audio...")
                # Create 1 second of silence as test audio
                test_audio = b'\x00' * 32000  # 1 second of silence at 16kHz 16-bit
                
                result = await voice_service.stt_processor.transcribe_audio(
                    audio_data=test_audio,
                    audio_format="pcm",
                    sample_rate=16000,
                    channels=1
                )
                debug_info["test_transcription"] = True
                debug_info["test_result_text"] = result.text
                debug_info["test_result_confidence"] = result.confidence
                debug_info["test_result_language"] = result.language_detected
                
            except Exception as e:
                debug_info["test_transcription_error"] = str(e)
                debug_info["test_transcription_error_type"] = type(e).__name__
                import traceback
                debug_info["test_transcription_traceback"] = traceback.format_exc()
                
        except Exception as e:
            debug_info["processor_error"] = str(e)
    
    return debug_info

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    print("Shutting down - cleaning up resources...")
    # Voice service cleanup happens automatically
    print("Shutdown cleanup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)