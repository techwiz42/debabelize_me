from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import uuid
import traceback
import tempfile
import os
from app.services.voice_service import voice_service
from app.database.database import Database
from app.utils.word_counter import count_words
from typing import Optional

async def handle_whisper_transcription(websocket: WebSocket, current_user: Optional[object] = None):
    """WebSocket handler for OpenAI Whisper using file-based transcription (non-streaming)."""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    # Buffer for collecting audio chunks
    audio_buffer = bytearray()
    buffer_timeout = None
    
    try:
        if not voice_service.stt_processor:
            print("ERROR: STT processor not initialized")
            await websocket.send_json({"error": "STT processor not initialized"})
            await websocket.close()
            return
        
        print(f"Started Whisper STT session: {session_id}")
        print(f"Processor type: {type(voice_service.stt_processor)}")
        
        async def process_buffered_audio():
            """Process collected audio buffer"""
            if len(audio_buffer) == 0:
                return
                
            try:
                print(f"Processing {len(audio_buffer)} bytes of buffered audio with Whisper")
                
                # Transcribe the buffered audio
                result = await voice_service.stt_processor.transcribe_audio(
                    audio_data=bytes(audio_buffer),
                    audio_format="wav",  # PCM format from frontend
                    sample_rate=16000,   # 16kHz from frontend
                    language="en"        # Primary language
                )
                
                print(f"Whisper transcription result: '{result.text}' (confidence: {result.confidence})")
                
                # Track words for usage statistics
                if result.text and current_user:
                    word_count = count_words(result.text)
                    if word_count > 0:
                        await Database.increment_usage_stats(
                            user_id=current_user.id,
                            stt_words=word_count
                        )
                        print(f"Tracked {word_count} STT words for user {current_user.email}")
                
                # Send result to frontend
                response_data = {
                    "text": result.text,
                    "is_final": True,  # Whisper always returns final results
                    "language": result.language_detected or "en",
                    "confidence": result.confidence,
                    "provider": "openai_whisper",
                    "cost_estimate": result.metadata.get("api_usage_seconds", 0) * 0.0001  # OpenAI pricing
                }
                
                # Only send non-empty results
                if result.text.strip():
                    print(f"Sending Whisper WebSocket response: {response_data}")
                    await websocket.send_json(response_data)
                    
                # Clear buffer after processing
                audio_buffer.clear()
                
            except Exception as e:
                print(f"Error processing buffered audio with Whisper: {e}")
                traceback.print_exc()
                await websocket.send_json({"error": f"Transcription failed: {str(e)}"})
        
        async def schedule_buffer_processing():
            """Schedule processing after a delay"""
            nonlocal buffer_timeout
            
            # Cancel existing timeout
            if buffer_timeout and not buffer_timeout.done():
                buffer_timeout.cancel()
            
            # Schedule new processing
            buffer_timeout = asyncio.create_task(asyncio.sleep(2.0))  # 2 second delay
            try:
                await buffer_timeout
                await process_buffered_audio()
            except asyncio.CancelledError:
                pass  # Timeout was cancelled, new audio arrived
        
        # Handle incoming audio data
        while True:
            try:
                # Receive audio data from frontend
                data = await asyncio.wait_for(websocket.receive_bytes(), timeout=30.0)
                
                if len(data) == 0:
                    # Keepalive ping - process buffer if we have audio
                    if len(audio_buffer) > 0:
                        await process_buffered_audio()
                    continue
                
                print(f"Received {len(data)} bytes for Whisper buffering")
                
                # Add to buffer
                audio_buffer.extend(data)
                
                # Schedule processing (will cancel previous if new audio arrives)
                asyncio.create_task(schedule_buffer_processing())
                
                # Process immediately if buffer gets large (>4 seconds of audio)
                max_buffer_size = 16000 * 2 * 4  # 4 seconds at 16kHz 16-bit
                if len(audio_buffer) >= max_buffer_size:
                    print("Buffer full, processing immediately")
                    await process_buffered_audio()
                
            except asyncio.TimeoutError:
                print(f"Whisper WebSocket timeout - no data received for 30s, session {session_id}")
                # Process any remaining buffered audio before closing
                if len(audio_buffer) > 0:
                    await process_buffered_audio()
                break
            except WebSocketDisconnect:
                print(f"Whisper WebSocket disconnected for session {session_id}")
                # Process any remaining buffered audio before closing
                if len(audio_buffer) > 0:
                    await process_buffered_audio()
                break
            except Exception as loop_error:
                print(f"Error in Whisper audio processing loop: {loop_error}")
                traceback.print_exc()
                break
        
        # Cancel any pending timeout
        if buffer_timeout and not buffer_timeout.done():
            buffer_timeout.cancel()
        
    except Exception as e:
        print(f"Whisper WebSocket error: {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        print(f"Cleaned up Whisper session: {session_id}")
        
        try:
            await websocket.close()
        except:
            pass