#!/usr/bin/env python3
"""
Direct test of Soniox streaming without the backend wrapper
"""

import asyncio
import json
import struct
import numpy as np
from debabelizer.providers.stt.soniox import SonioxSTTProvider

# Use the API key from the environment
SONIOX_API_KEY = "cfb7e338d94102d7b59deea599b238e4ae2fa8085830097c7e3ed89696c4ec95"

def generate_test_audio():
    """Generate a simple test audio chunk"""
    # Generate 1 second of clear 440Hz sine wave
    sample_rate = 16000
    duration = 1.0  # 1 second
    frequency = 440
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    pcm = (wave * 16000).astype(np.int16)
    
    return struct.pack(f'{len(pcm)}h', *pcm)

async def test_direct_soniox():
    """Test Soniox streaming directly"""
    print("Testing direct Soniox streaming connection...")
    
    try:
        # Initialize Soniox provider
        soniox = SonioxSTTProvider(SONIOX_API_KEY)
        
        print("✅ Soniox provider initialized")
        
        # Start streaming session
        print("Starting Soniox streaming session...")
        session_id = await soniox.start_streaming(
            audio_format="pcm",
            sample_rate=16000,
            language="en"
        )
        
        print(f"✅ Soniox session started: {session_id}")
        
        # Generate and send test audio
        test_audio = generate_test_audio()
        print(f"Sending {len(test_audio)} bytes of test audio...")
        
        # Send in chunks
        chunk_size = 1024
        for i in range(0, len(test_audio), chunk_size):
            chunk = test_audio[i:i + chunk_size]
            await soniox.stream_audio(session_id, chunk)
            print(f"Sent chunk {i//chunk_size + 1}")
            await asyncio.sleep(0.1)
        
        print("Waiting for Soniox transcription results...")
        
        # Get results
        results = []
        try:
            async for result in soniox.get_streaming_results(session_id):
                print(f"📝 Result: '{result.text}' (final: {result.is_final}, confidence: {result.confidence})")
                results.append(result)
                
                # Break after getting a few results or a final result
                if len(results) >= 5 or result.is_final:
                    break
                    
        except Exception as results_error:
            print(f"Error getting results: {results_error}")
            import traceback
            traceback.print_exc()
        
        # Stop session
        await soniox.stop_streaming(session_id)
        print(f"✅ Stopped Soniox session: {session_id}")
        
        print(f"Got {len(results)} results total")
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_soniox())
    if success:
        print("✅ Direct Soniox test successful!")
    else:
        print("❌ Direct Soniox test failed!")