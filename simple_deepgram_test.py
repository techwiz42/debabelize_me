#!/usr/bin/env python3
"""
Simple direct test of Deepgram WebSocket streaming
"""

import asyncio
import json
import struct
import numpy as np
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

# Use the API key from the environment
DEEPGRAM_API_KEY = "8f02a850f9cb7214c0a269f531ad4da461866987"

def generate_test_audio():
    """Generate a simple test audio chunk"""
    # Generate 32ms of 440Hz sine wave
    sample_rate = 16000
    duration = 0.032  # 32ms
    frequency = 440
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.3 * np.sin(2 * np.pi * frequency * t)
    pcm = (wave * 32767).astype(np.int16)
    
    return struct.pack(f'{len(pcm)}h', *pcm)

async def test_direct_deepgram():
    """Test Deepgram streaming directly"""
    print("Testing direct Deepgram WebSocket connection...")
    
    try:
        # Initialize client
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        
        # Create connection
        dg_connection = deepgram.listen.websocket.v("1")
        
        # Results storage
        results = []
        connected = False
        
        # Event handlers
        def on_open(self, open, **kwargs):
            nonlocal connected
            print("✅ Deepgram WebSocket opened")
            connected = True
        
        def on_message(self, result, **kwargs):
            print(f"📝 Received result: {result}")
            results.append(result)
            
        def on_error(self, error, **kwargs):
            print(f"❌ Deepgram error: {error}")
            
        def on_close(self, close, **kwargs):
            nonlocal connected
            print("🔒 Deepgram WebSocket closed")
            connected = False
        
        # Register handlers
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        
        # Configure options
        options = LiveOptions(
            model="nova-2",
            language="en-US",
            punctuate=True,
            interim_results=True,
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            vad_events=True
        )
        
        # Start connection
        print("Starting Deepgram connection...")
        if dg_connection.start(options):
            print("✅ Connection start returned True")
            
            # Wait for connection
            for i in range(10):  # Wait up to 1 second
                if connected:
                    break
                await asyncio.sleep(0.1)
            
            if connected:
                print("✅ Connection established!")
                
                # Send some test audio
                test_audio = generate_test_audio()
                print(f"Sending {len(test_audio)} bytes of test audio...")
                
                for i in range(10):  # Send 10 chunks
                    dg_connection.send(test_audio)
                    await asyncio.sleep(0.1)
                
                # Wait for results
                print("Waiting for transcription results...")
                await asyncio.sleep(2)
                
                # Send close message
                dg_connection.finish()
                
                print(f"Received {len(results)} results")
                for result in results:
                    print(f"Result: {result}")
                    
            else:
                print("❌ Failed to establish connection")
        else:
            print("❌ Connection start returned False")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_deepgram())