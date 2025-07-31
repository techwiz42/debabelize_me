#!/usr/bin/env python3
"""
Test script for Soniox WebSocket streaming implementation
"""

import asyncio
import websockets
import numpy as np
import struct
import json
import time

# Configuration
WS_URL = "wss://debabelize.me/api/ws/stt"
SAMPLE_RATE = 16000
CHUNK_SIZE = 512  # samples per chunk (32ms at 16kHz)

def generate_speech_audio():
    """Generate more realistic speech-like audio for Soniox"""
    chunks = []
    
    # Generate complex audio pattern that should trigger Soniox transcription
    # Simulate speaking "hello soniox" with varying frequencies and amplitudes
    
    # "Hello" - vowel sounds with formants
    for i in range(25):  # ~800ms
        t = np.linspace(0, 0.032, int(SAMPLE_RATE * 0.032), False)
        
        # Fundamental at ~180Hz (clearer voice)
        fundamental = 0.4 * np.sin(2 * np.pi * 180 * t)
        
        # Add formants for vowel sounds (more pronounced)
        formant1 = 0.3 * np.sin(2 * np.pi * 900 * t)  # First formant
        formant2 = 0.2 * np.sin(2 * np.pi * 1400 * t)  # Second formant
        formant3 = 0.1 * np.sin(2 * np.pi * 2100 * t)  # Third formant
        
        # Combine with harmonic content
        wave = fundamental + formant1 + formant2 + formant3
        
        # Add some noise for realism
        wave += np.random.normal(0, 0.03, len(t))
        
        # Apply speech-like envelope
        envelope = np.exp(-t * 1.5) * 0.7 + 0.3
        wave *= envelope
        
        # Boost amplitude for better detection
        pcm = (wave * 20000).astype(np.int16)
        chunks.append(struct.pack(f'{len(pcm)}h', *pcm))
    
    # Short pause
    for _ in range(3):
        silence = np.zeros(int(SAMPLE_RATE * 0.032))
        pcm_silence = silence.astype(np.int16)
        chunks.append(struct.pack(f'{len(pcm_silence)}h', *pcm_silence))
    
    # "Soniox" - different vowel pattern
    for i in range(20):  # ~640ms
        t = np.linspace(0, 0.032, int(SAMPLE_RATE * 0.032), False)
        
        # Different fundamental for variety
        fundamental = 0.4 * np.sin(2 * np.pi * 160 * t)
        
        # Different formants for "soniox"
        formant1 = 0.25 * np.sin(2 * np.pi * 700 * t)
        formant2 = 0.15 * np.sin(2 * np.pi * 1200 * t)
        formant3 = 0.1 * np.sin(2 * np.pi * 1800 * t)
        
        wave = fundamental + formant1 + formant2 + formant3
        wave += np.random.normal(0, 0.03, len(t))
        
        # Fade out envelope
        envelope = np.exp(-t * 1.2) * 0.8 + 0.2
        wave *= envelope
        
        pcm = (wave * 20000).astype(np.int16)
        chunks.append(struct.pack(f'{len(pcm)}h', *pcm))
    
    return chunks

async def test_soniox_streaming():
    """Test Soniox streaming with detailed output"""
    print("🎤 Soniox Streaming Test")
    print("========================")
    print(f"WebSocket URL: {WS_URL}")
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print()
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"✅ Connected to {WS_URL}")
            
            received_messages = []
            
            # Start receiving results
            async def receive_and_log():
                try:
                    while True:
                        message = await websocket.recv()
                        received_messages.append(message)
                        
                        try:
                            data = json.loads(message)
                            print(f"📨 SONIOX RESULT: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError:
                            print(f"📨 RECEIVED (non-JSON): {message}")
                            
                except websockets.exceptions.ConnectionClosed:
                    print("🔒 WebSocket connection closed")
                except Exception as e:
                    print(f"❌ Error in receiver: {e}")
            
            # Start receiver
            receive_task = asyncio.create_task(receive_and_log())
            
            print("\n🎤 Sending speech-like audio to Soniox...")
            
            # Send keepalive
            await websocket.send(b'')
            await asyncio.sleep(0.1)
            
            # Send speech-like audio
            speech_chunks = generate_speech_audio()
            print(f"Generated {len(speech_chunks)} audio chunks")
            
            start_time = time.time()
            for i, chunk in enumerate(speech_chunks):
                await websocket.send(chunk)
                if i % 15 == 0:
                    print(f"📤 Sent chunk {i+1}/{len(speech_chunks)}")
                await asyncio.sleep(0.032)  # 32ms timing to match real-time
            
            total_time = time.time() - start_time
            print(f"✅ Finished sending {len(speech_chunks)} chunks in {total_time:.2f}s")
            print("⏳ Waiting for Soniox transcription results...")
            
            # Wait longer for Soniox to process
            await asyncio.sleep(5)
            
            # Cancel receiver
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            
            print(f"\n📊 Summary: Received {len(received_messages)} messages from Soniox")
            if received_messages:
                print("✅ Soniox streaming successful!")
                
                # Analyze results
                transcriptions = []
                for msg in received_messages:
                    try:
                        data = json.loads(msg)
                        if data.get('text') and data.get('provider') == 'soniox':
                            transcriptions.append({
                                'text': data['text'],
                                'is_final': data.get('is_final', False),
                                'confidence': data.get('confidence', 0.0)
                            })
                    except:
                        pass
                
                if transcriptions:
                    print(f"🎯 Got {len(transcriptions)} transcription results:")
                    for i, t in enumerate(transcriptions):
                        final_marker = "FINAL" if t['is_final'] else "INTERIM"
                        print(f"  {i+1}. [{final_marker}] '{t['text']}' (confidence: {t['confidence']:.2f})")
                else:
                    print("⚠️ No transcription text found in responses")
            else:
                print("❌ No messages received from Soniox - check connection or audio format")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_simple_soniox_connection():
    """Test basic Soniox connection without audio"""
    print("Testing simple Soniox WebSocket connection...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ Successfully connected!")
            
            # Send empty keepalive
            await websocket.send(b'')
            print("✅ Sent keepalive")
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received response: {response}")
            except asyncio.TimeoutError:
                print("⏱️ No response within 5 seconds (this might be normal)")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("🔧 First, let's switch to Soniox STT provider...")
    print("Make sure DEBABELIZER_STT_PROVIDER=soniox in backend/.env")
    print()
    
    # Run tests
    asyncio.run(test_simple_soniox_connection())
    print()
    asyncio.run(test_soniox_streaming())