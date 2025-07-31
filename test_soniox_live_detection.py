#!/usr/bin/env python3
"""
Test Soniox language auto-detection with live WebSocket streaming
"""

import asyncio
import websockets
import json
import struct
import numpy as np

# Generate more realistic speech-like audio patterns
def generate_realistic_speech_audio(language_pattern="english", duration=3.0):
    """Generate audio that mimics different language patterns"""
    sample_rate = 16000
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, False)
    
    if language_pattern == "english":
        # English: moderate pitch variation, clear pauses
        base_freq = 180 + 60 * np.sin(2 * np.pi * 0.8 * t)
        formants = (
            0.4 * np.sin(2 * np.pi * 700 * t) +  # Lower formant
            0.3 * np.sin(2 * np.pi * 1200 * t) + # Higher formant
            0.2 * np.sin(2 * np.pi * 2400 * t)   # Consonant clarity
        )
        # Add pauses typical of English speech
        envelope = np.ones_like(t)
        for pause in [0.7, 1.4, 2.1]:
            mask = (t >= pause) & (t < pause + 0.15)
            envelope[mask] = 0.1
            
    elif language_pattern == "tonal":
        # Tonal languages: more pitch variation, shorter pauses
        base_freq = 200 + 120 * np.sin(2 * np.pi * 1.2 * t) * np.sin(2 * np.pi * 0.3 * t)
        formants = (
            0.5 * np.sin(2 * np.pi * 600 * t) +
            0.4 * np.sin(2 * np.pi * 1000 * t) +
            0.3 * np.sin(2 * np.pi * 1800 * t)
        )
        envelope = np.ones_like(t)
        for pause in [0.9, 1.8]:
            mask = (t >= pause) & (t < pause + 0.1)
            envelope[mask] = 0.2
            
    elif language_pattern == "romantic":
        # Romance languages: flowing, less harsh consonants
        base_freq = 160 + 40 * np.sin(2 * np.pi * 0.6 * t)
        formants = (
            0.5 * np.sin(2 * np.pi * 650 * t) +
            0.4 * np.sin(2 * np.pi * 1100 * t) +
            0.2 * np.sin(2 * np.pi * 2000 * t)
        )
        envelope = np.ones_like(t)
        for pause in [0.8, 1.6, 2.4]:
            mask = (t >= pause) & (t < pause + 0.12)
            envelope[mask] = 0.15
            
    else: # "germanic"
        # Germanic languages: sharper consonants, distinctive rhythm
        base_freq = 170 + 50 * np.sin(2 * np.pi * 0.9 * t)
        formants = (
            0.4 * np.sin(2 * np.pi * 750 * t) +
            0.3 * np.sin(2 * np.pi * 1300 * t) +
            0.3 * np.sin(2 * np.pi * 2600 * t)  # Sharp consonants
        )
        envelope = np.ones_like(t)
        for pause in [0.6, 1.3, 2.0]:
            mask = (t >= pause) & (t < pause + 0.18)
            envelope[mask] = 0.05
    
    # Combine components
    audio = envelope * (
        0.6 * np.sin(2 * np.pi * base_freq * t) +
        0.4 * formants +
        0.1 * np.random.normal(0, 1, num_samples)  # Background noise
    )
    
    # Convert to 16-bit PCM
    audio = np.clip(audio, -1.0, 1.0)
    pcm_data = (audio * 16000).astype(np.int16)
    
    return struct.pack(f'{len(pcm_data)}h', *pcm_data)

async def test_language_detection_via_websocket():
    """Test language auto-detection via the backend WebSocket"""
    
    print("🌐 Testing Soniox Language Auto-Detection via WebSocket")
    print("=" * 60)
    
    # Test cases with different speech patterns
    test_cases = [
        {
            "name": "English-like Pattern",
            "pattern": "english",
            "expected": "Should detect as English or similar Germanic language"
        },
        {
            "name": "Tonal Language Pattern", 
            "pattern": "tonal",
            "expected": "Might detect as Chinese, Vietnamese, or Thai"
        },
        {
            "name": "Romance Language Pattern",
            "pattern": "romantic", 
            "expected": "Might detect as Spanish, French, Italian, or Portuguese"
        },
        {
            "name": "Germanic Language Pattern",
            "pattern": "germanic",
            "expected": "Might detect as German, Dutch, or similar"
        }
    ]
    
    backend_ws_url = "wss://debabelize.me/api/ws/stt"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"Expected: {test_case['expected']}")
        print("-" * 50)
        
        try:
            # Connect to backend WebSocket
            async with websockets.connect(backend_ws_url) as websocket:
                print("✅ Connected to backend WebSocket")
                
                # Generate speech-like audio
                print(f"Generating {test_case['pattern']} speech pattern...")
                audio_data = generate_realistic_speech_audio(
                    test_case['pattern'], 
                    duration=4.0
                )
                
                # Send audio in chunks
                chunk_size = 1600  # 100ms chunks at 16kHz
                chunks_sent = 0
                
                print("Streaming audio chunks...")
                for offset in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[offset:offset + chunk_size]
                    await websocket.send(chunk)
                    chunks_sent += 1
                    await asyncio.sleep(0.1)  # 100ms between chunks
                
                print(f"Sent {chunks_sent} audio chunks")
                
                # Wait for transcription results
                print("Waiting for transcription results...")
                results = []
                timeout_count = 0
                max_timeout = 50  # 5 seconds
                
                while timeout_count < max_timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        
                        try:
                            data = json.loads(message)
                            results.append(data)
                            
                            print(f"📝 Received: {data}")
                            
                            # Look for language detection info
                            if 'language' in data:
                                print(f"🌐 Detected Language: {data['language']}")
                            if 'confidence' in data:
                                print(f"📊 Confidence: {data['confidence']}")
                            if 'metadata' in data and data['metadata']:
                                print(f"📋 Metadata: {data['metadata']}")
                                
                            # If we get a final result, we can stop
                            if data.get('is_final', False):
                                print("✅ Received final result")
                                break
                                
                        except json.JSONDecodeError:
                            print(f"📨 Non-JSON message: {message}")
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        if timeout_count % 10 == 0:
                            print(f"⏳ Still waiting... ({timeout_count/10:.1f}s)")
                
                # Summary
                print(f"\n📊 Test {i} Summary:")
                if results:
                    print(f"  • Received {len(results)} results")
                    final_results = [r for r in results if r.get('is_final', False)]
                    if final_results:
                        final_text = final_results[-1].get('text', 'No text')
                        print(f"  • Final transcription: '{final_text}'")
                    else:
                        print("  • No final transcription received")
                    
                    # Check for any language detection
                    lang_results = [r for r in results if 'language' in r]
                    if lang_results:
                        detected_lang = lang_results[-1]['language']
                        print(f"  • Detected language: {detected_lang}")
                    else:
                        print("  • No language detection info received")
                else:
                    print("  • No results received")
                    
        except Exception as e:
            print(f"❌ Error in test {i}: {e}")
            import traceback
            traceback.print_exc()
        
        print()  # Add spacing between tests
    
    print("=" * 60)
    print("🏁 Language detection testing complete")
    print("\n💡 Note: Language auto-detection depends on:")
    print("  • Audio quality and clarity")
    print("  • Length of audio sample") 
    print("  • Presence of actual speech vs synthetic patterns")
    print("  • Provider's confidence thresholds")

if __name__ == "__main__":
    asyncio.run(test_language_detection_via_websocket())