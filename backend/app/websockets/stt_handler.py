from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import uuid
import struct
import traceback
from app.services.voice_service import voice_service
from app.utils.audio_processing import audio_buffer_manager, AUDIO_BUFFER_CONFIG

async def handle_stt_websocket(websocket: WebSocket):
    """WebSocket endpoint for buffered STT using fake streaming approach."""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    # Initialize buffering session
    audio_buffer_manager.create_session(session_id)
    
    try:
        if not voice_service.stt_processor:
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
                if not audio_buffer_manager.add_audio_data(session_id, data, current_time):
                    print(f"Failed to add audio data for session {session_id}")
                    continue
                
                # Check if we should process the buffer
                if audio_buffer_manager.should_process_buffer(session_id, current_time):
                    # Extract buffered audio
                    buffered_audio = audio_buffer_manager.extract_buffer(session_id, current_time)
                    
                    print(f"Processing {len(buffered_audio)} bytes of buffered audio")
                    
                    # Debug: Check if audio is just silence
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
                        traceback.print_exc()
                    
                    try:
                        # Process raw PCM data directly - faster than WAV conversion
                        result = await voice_service.stt_processor.transcribe_chunk(
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
        # Process any remaining audio in buffer before cleanup
        final_audio = audio_buffer_manager.get_final_buffer(session_id)
        if len(final_audio) > 0:
            try:
                print(f"Processing final {len(final_audio)} bytes before cleanup")
                result = await voice_service.stt_processor.transcribe_chunk(
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
        
        audio_buffer_manager.cleanup_session(session_id)
        print(f"Cleaned up buffering session: {session_id}")
        
        try:
            await websocket.close()
        except:
            pass