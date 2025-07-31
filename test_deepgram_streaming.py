#!/usr/bin/env python3
"""
Test script to mock frontend WebSocket connection and test Deepgram true streaming
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
DURATION = 5  # seconds of audio to generate

def generate_audio_chunk(frequency=440, duration_ms=32, sample_rate=16000, amplitude=0.3):
    """Generate a sine wave audio chunk to simulate speech"""
    duration_sec = duration_ms / 1000
    num_samples = int(sample_rate * duration_sec)
    
    # Generate sine wave
    t = np.linspace(0, duration_sec, num_samples, False)
    # Add some variation to simulate speech
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    # Add harmonics
    wave += 0.1 * amplitude * np.sin(4 * np.pi * frequency * t)
    wave += 0.05 * amplitude * np.sin(6 * np.pi * frequency * t)
    
    # Add some noise
    noise = np.random.normal(0, 0.01, num_samples)
    wave += noise
    
    # Convert to 16-bit PCM
    pcm = (wave * 32767).astype(np.int16)
    
    # Convert to bytes
    return struct.pack(f'{len(pcm)}h', *pcm)

def generate_speech_pattern():
    """Generate audio that mimics speech patterns"""
    chunks = []
    
    # Simulate "Hello World" pattern
    # "Hello" - rising tone
    for i in range(10):  # ~320ms
        freq = 200 + i * 20  # Rising frequency
        chunks.append(generate_audio_chunk(freq, amplitude=0.4))
    
    # Pause between words
    for i in range(5):  # ~160ms silence
        chunks.append(generate_audio_chunk(0, amplitude=0))
    
    # "World" - falling tone  
    for i in range(10):  # ~320ms
        freq = 400 - i * 20  # Falling frequency
        chunks.append(generate_audio_chunk(freq, amplitude=0.4))
    
    return chunks

async def test_streaming():
    """Test the Deepgram streaming implementation"""
    print("Connecting to WebSocket STT endpoint...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"Connected to {WS_URL}")
            
            # Start receiving results in background
            async def receive_results():
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        if data.get("error"):
                            print(f"❌ Error: {data['error']}")
                        else:
                            is_final = data.get("is_final", False)
                            text = data.get("text", "")
                            confidence = data.get("confidence", 0)
                            
                            if text or is_final:
                                status = "FINAL" if is_final else "INTERIM"
                                print(f"[{status}] Text: '{text}' (confidence: {confidence:.2f})")
                                
                                # Show metadata if available
                                if data.get("words"):
                                    print(f"  Words: {len(data['words'])} detected")
                                if data.get("duration"):
                                    print(f"  Duration: {data['duration']:.2f}s")
                                    
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket connection closed")
                except Exception as e:
                    print(f"Error receiving results: {e}")
            
            # Start result receiver
            receive_task = asyncio.create_task(receive_results())
            
            print("\n📢 Streaming test audio...")
            print("=" * 50)
            
            # Send keepalive first
            await websocket.send(b'')
            await asyncio.sleep(0.1)
            
            # Test 1: Send speech-like pattern
            print("\nTest 1: Speech pattern simulation")
            speech_chunks = generate_speech_pattern()
            
            for i, chunk in enumerate(speech_chunks):
                await websocket.send(chunk)
                print(f".", end="", flush=True)
                await asyncio.sleep(0.032)  # 32ms between chunks
            
            print("\n\nWaiting for final results...")
            await asyncio.sleep(2)
            
            # Test 2: Continuous tone (should trigger VAD)
            print("\nTest 2: Continuous tone test")
            for i in range(50):  # ~1.6 seconds
                chunk = generate_audio_chunk(300, amplitude=0.5)
                await websocket.send(chunk)
                if i % 10 == 0:
                    print(f".", end="", flush=True)
                await asyncio.sleep(0.032)
            
            print("\n\nWaiting for final results...")
            await asyncio.sleep(2)
            
            # Test 3: Silence (should trigger utterance end)
            print("\nTest 3: Silence test")
            for i in range(30):  # ~1 second of silence
                chunk = generate_audio_chunk(0, amplitude=0)
                await websocket.send(chunk)
                await asyncio.sleep(0.032)
            
            print("\nTest complete! Waiting for any remaining results...")
            await asyncio.sleep(2)
            
            # Cancel receiver
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()

async def test_simple_connection():
    """Test basic WebSocket connection"""
    print("Testing basic WebSocket connection...")
    
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
                print("⏱️  No response within 5 seconds (this might be normal)")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

async def main():
    """Run all tests"""
    print("🎤 Deepgram True Streaming Test")
    print("================================")
    print(f"WebSocket URL: {WS_URL}")
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"Chunk Size: {CHUNK_SIZE} samples")
    print()
    
    # Test basic connection first
    await test_simple_connection()
    print()
    
    # Run main streaming test
    await test_streaming()
    
    print("\n✅ All tests complete!")

if __name__ == "__main__":
    asyncio.run(main())