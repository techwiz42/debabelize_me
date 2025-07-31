from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import uuid
import traceback
from app.services.voice_service import voice_service

async def handle_soniox_streaming(websocket: WebSocket):
    """WebSocket handler for Soniox using real streaming (native streaming support)."""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    stt_session_id = None
    
    try:
        if not voice_service.stt_processor:
            print("ERROR: STT processor not initialized")
            await websocket.send_json({"error": "STT processor not initialized"})
            await websocket.close()
            return
        
        print(f"Started Soniox real streaming STT session: {session_id}")
        print(f"Processor type: {type(voice_service.stt_processor)}")
        
        # Start Soniox streaming session using correct method name
        try:
            print("Attempting to start Soniox streaming...")
            stt_session_id = await voice_service.stt_processor.start_streaming(
                audio_format="pcm",      # PCM format from frontend
                sample_rate=16000,       # 16kHz from frontend  
                language="en",           # Primary language
                has_pending_audio=True   # Indicate we expect more audio
            )
            print(f"SUCCESS: Soniox streaming session started: {stt_session_id}")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to start Soniox streaming session: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            await websocket.send_json({"error": f"Failed to start streaming: {str(e)}"})
            await websocket.close()
            return
        
        # Create task to handle streaming results
        async def handle_streaming_results():
            try:
                print(f"Starting to listen for streaming results from session {stt_session_id}")
                async for result in voice_service.stt_processor.get_streaming_results(stt_session_id):
                    print(f"Soniox streaming result: '{result.text}' (final: {result.is_final}, confidence: {getattr(result, 'confidence', 0.0)})")
                    
                    # Send result to frontend
                    response_data = {
                        "text": result.text,
                        "is_final": result.is_final,
                        "language": getattr(result, 'language_detected', 'en'),
                        "confidence": getattr(result, 'confidence', 0.0),
                        "provider": "soniox"
                    }
                    
                    # Only send non-empty results
                    if result.text.strip():
                        print(f"Sending Soniox WebSocket response: {response_data}")
                        await websocket.send_json(response_data)
                        
                print(f"Streaming results loop ended for session {stt_session_id}")
            except Exception as e:
                print(f"CRITICAL: Error handling Soniox streaming results: {e}")
                print(f"Error type: {type(e)}")
                traceback.print_exc()
        
        # Start the results handler task
        results_task = asyncio.create_task(handle_streaming_results())
        
        # Handle incoming audio data
        while True:
            try:
                # Receive audio data from frontend
                data = await asyncio.wait_for(websocket.receive_bytes(), timeout=60.0)
                
                if len(data) == 0:
                    # Keepalive ping - continue silently
                    continue
                
                print(f"Streaming {len(data)} bytes to Soniox")
                
                # Stream audio data directly to Soniox (real streaming) - using correct method name
                try:
                    await voice_service.stt_processor.stream_audio(stt_session_id, data)
                except Exception as stream_error:
                    print(f"Error streaming audio chunk to Soniox: {stream_error}")
                    traceback.print_exc()
                    # Continue processing - don't break on individual chunk errors
                
            except asyncio.TimeoutError:
                print(f"Soniox WebSocket timeout - no data received for 60s, session {session_id}")
                break
            except WebSocketDisconnect:
                print(f"Soniox WebSocket disconnected for session {session_id}")
                break
            except Exception as loop_error:
                print(f"Error in Soniox audio processing loop: {loop_error}")
                traceback.print_exc()
                break
        
        # Cancel the results task
        if not results_task.done():
            results_task.cancel()
            try:
                await results_task
            except asyncio.CancelledError:
                pass
        
    except Exception as e:
        print(f"Soniox WebSocket error: {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        # Stop Soniox streaming session using correct method name
        if stt_session_id:
            try:
                print(f"Stopping Soniox streaming session: {stt_session_id}")
                await voice_service.stt_processor.stop_streaming(stt_session_id)
            except Exception as cleanup_error:
                print(f"Error stopping Soniox streaming session: {cleanup_error}")
        
        print(f"Cleaned up Soniox streaming session: {session_id}")
        
        try:
            await websocket.close()
        except:
            pass