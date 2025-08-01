from fastapi import WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.services.voice_service import voice_service
from app.websockets.deepgram_handler import handle_deepgram_streaming
from app.websockets.soniox_handler import handle_soniox_streaming
from app.websockets.whisper_handler import handle_whisper_transcription
from app.services.auth_service import auth_service
from typing import Optional

async def handle_stt_websocket(websocket: WebSocket):
    """WebSocket endpoint that routes to provider-specific streaming handlers with fallback."""
    
    # Extract session token from query parameters
    session_token = websocket.query_params.get("session_token")
    current_user = None
    
    print(f"STT WebSocket - Session token present: {session_token is not None}")
    if session_token:
        print(f"STT WebSocket - Session token: {session_token[:10]}...")
        current_user = await auth_service.validate_session(session_token)
        if current_user:
            print(f"STT WebSocket - Authenticated user: {current_user.email}")
        else:
            print("STT WebSocket - Session token validation failed")
    else:
        print("STT WebSocket - No session token provided")
    
    # Ensure voice service is initialized before routing
    print("Checking voice service initialization...")
    if not voice_service.stt_processor or not voice_service.tts_processor:
        print("Voice service not initialized, initializing now...")
        await voice_service.initialize_processors()
    
    # Route to appropriate streaming handler based on configured provider
    provider = settings.debabelizer_stt_provider.lower()
    
    if provider == "soniox":
        print("Routing to Soniox streaming handler")
        try:
            await handle_soniox_streaming(websocket, current_user)
        except Exception as soniox_error:
            print(f"Soniox streaming failed: {soniox_error}")
            print("Falling back to Deepgram streaming")
            try:
                # Close the websocket that failed and let frontend reconnect
                await websocket.send_json({"error": "Soniox failed, please reconnect for Deepgram fallback"})
                await websocket.close()
            except:
                pass
    elif provider == "deepgram":
        print("Routing to Deepgram streaming handler")
        await handle_deepgram_streaming(websocket, current_user)
    elif provider == "openai_whisper":
        print("Routing to OpenAI Whisper handler")
        await handle_whisper_transcription(websocket, current_user)
    else:
        # Fallback to Deepgram approach for other providers
        print(f"Unknown provider '{provider}', falling back to Deepgram streaming")
        await handle_deepgram_streaming(websocket, current_user)
    
