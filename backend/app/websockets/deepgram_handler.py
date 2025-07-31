from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import traceback
from app.services.voice_service import voice_service
from app.utils.audio_processing import AUDIO_BUFFER_CONFIG

async def handle_deepgram_streaming(websocket: WebSocket):
    """WebSocket handler for Deepgram using true WebSocket streaming."""
    await websocket.accept()
    session_id = None
    streaming_task = None
    
    try:
        if not voice_service.stt_processor:
            await websocket.send_json({"error": "STT processor not initialized"})
            return
        
        # Start streaming session
        session_id = await voice_service.stt_processor.start_streaming_transcription(
            audio_format="pcm",
            sample_rate=AUDIO_BUFFER_CONFIG["sample_rate"],
            channels=AUDIO_BUFFER_CONFIG["channels"],
            interim_results=True,
            punctuate=True,
            smart_format=True,
            vad_events=True,
            utterance_end_ms=1500
        )
        
        print(f"Started Deepgram true streaming session: {session_id}")
        
        # Start a task to handle streaming results
        async def process_streaming_results():
            try:
                async for result in voice_service.stt_processor.get_streaming_results(session_id):
                    # Handle VAD events (indicated by special text markers)
                    if result.text == "[SPEECH_STARTED]":
                        print("Speech started detected")
                        # Could send a signal to frontend if needed
                        continue
                    elif result.text == "[UTTERANCE_END]":
                        print("Utterance end detected")
                        # Could send utterance end signal
                        continue
                    
                    # Handle transcription results
                    if result.text or result.is_final:
                        response_data = {
                            "text": result.text,
                            "is_final": result.is_final,
                            "confidence": result.confidence,
                            "provider": "deepgram",
                            "streaming": True,  # Indicate true streaming
                            "session_id": result.session_id
                        }
                        
                        print(f"Sending Deepgram streaming result: {response_data}")
                        await websocket.send_json(response_data)
                        
            except Exception as e:
                print(f"Error in streaming results processor: {e}")
                traceback.print_exc()
        
        # Start the results processor
        streaming_task = asyncio.create_task(process_streaming_results())
        
        # Handle incoming audio
        while True:
            try:
                # Receive audio data with timeout
                data = await asyncio.wait_for(websocket.receive_bytes(), timeout=60.0)
                
                if len(data) == 0:
                    # Keepalive ping
                    continue
                
                # Stream audio directly to Deepgram
                await voice_service.stt_processor.stream_audio(session_id, data)
                
            except asyncio.TimeoutError:
                print(f"WebSocket timeout - no data received for 60s, session {session_id}")
                break
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for session {session_id}")
                break
            except Exception as loop_error:
                print(f"Error in Deepgram streaming audio loop: {loop_error}")
                traceback.print_exc()
                break
        
    except Exception as e:
        print(f"Deepgram streaming WebSocket error: {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        # Cancel streaming task
        if streaming_task and not streaming_task.done():
            streaming_task.cancel()
            try:
                await streaming_task
            except asyncio.CancelledError:
                pass
        
        # Stop streaming session
        if session_id:
            try:
                await voice_service.stt_processor.stop_streaming_transcription(session_id)
                print(f"Stopped Deepgram streaming session: {session_id}")
            except Exception as cleanup_error:
                print(f"Error stopping Deepgram streaming session: {cleanup_error}")
        
        try:
            await websocket.close()
        except:
            pass