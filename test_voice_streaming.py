#!/usr/bin/env python3
"""
Enhanced test to check if we're receiving any transcription results
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

def generate_speech_audio():
    """Generate more realistic speech-like audio"""
    chunks = []
    
    # Generate more complex audio pattern that might trigger transcription
    # Simulate speaking "hello world" with varying frequencies and amplitudes
    
    # "Hello" - vowel sounds with formants
    for i in range(20):  # ~640ms
        # Mix fundamental frequency with formants
        t = np.linspace(0, 0.032, int(SAMPLE_RATE * 0.032), False)
        
        # Fundamental at ~150Hz (male voice)
        fundamental = 0.3 * np.sin(2 * np.pi * 150 * t)
        
        # Add formants for vowel sounds
        formant1 = 0.2 * np.sin(2 * np.pi * 800 * t)  # First formant
        formant2 = 0.1 * np.sin(2 * np.pi * 1200 * t)  # Second formant
        
        # Combine and add noise
        wave = fundamental + formant1 + formant2
        wave += np.random.normal(0, 0.05, len(t))  # More noise
        
        # Apply envelope to make it more speech-like
        envelope = np.exp(-t * 2) * 0.5 + 0.5
        wave *= envelope
        
        pcm = (wave * 16000).astype(np.int16)
        chunks.append(struct.pack(f'{len(pcm)}h', *pcm))
    
    # Pause
    silence = np.zeros(int(SAMPLE_RATE * 0.1))
    pcm_silence = silence.astype(np.int16)
    chunks.append(struct.pack(f'{len(pcm_silence)}h', *pcm_silence))
    
    # "World" - different vowel pattern
    for i in range(15):  # ~480ms
        t = np.linspace(0, 0.032, int(SAMPLE_RATE * 0.032), False)
        
        # Lower fundamental
        fundamental = 0.3 * np.sin(2 * np.pi * 120 * t)
        
        # Different formants for "world"
        formant1 = 0.2 * np.sin(2 * np.pi * 600 * t)
        formant2 = 0.1 * np.sin(2 * np.pi * 1000 * t)
        
        wave = fundamental + formant1 + formant2
        wave += np.random.normal(0, 0.05, len(t))
        
        # Fade out envelope
        envelope = np.exp(-t * 1.5) * 0.6 + 0.4
        wave *= envelope
        
        pcm = (wave * 16000).astype(np.int16)
        chunks.append(struct.pack(f'{len(pcm)}h', *pcm))
    
    return chunks

async def test_with_verbose_output():
    """Test with detailed output of all received messages"""
    print("Testing WebSocket STT with verbose output...")
    
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
                            print(f"📨 RECEIVED: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError:
                            print(f"📨 RECEIVED (non-JSON): {message}")
                            
                except websockets.exceptions.ConnectionClosed:
                    print("🔒 WebSocket connection closed")
                except Exception as e:
                    print(f"❌ Error in receiver: {e}")
            
            # Start receiver
            receive_task = asyncio.create_task(receive_and_log())
            
            print("\n🎤 Sending speech-like audio...")
            
            # Send keepalive
            await websocket.send(b'')
            await asyncio.sleep(0.1)
            
            # Send speech-like audio
            speech_chunks = generate_speech_audio()
            print(f"Generated {len(speech_chunks)} audio chunks")
            
            for i, chunk in enumerate(speech_chunks):
                await websocket.send(chunk)
                if i % 10 == 0:
                    print(f"Sent chunk {i+1}/{len(speech_chunks)}")
                await asyncio.sleep(0.032)  # 32ms timing
            
            print("✅ Finished sending audio, waiting for results...")
            await asyncio.sleep(3)  # Wait longer for results
            
            # Cancel receiver
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            
            print(f"\n📊 Summary: Received {len(received_messages)} messages")
            if received_messages:
                print("Messages received successfully!")
            else:
                print("⚠️ No messages received - check connection or audio format")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_with_verbose_output())