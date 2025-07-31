#!/usr/bin/env python3
"""
Test Soniox streaming language auto-detection with synthetic audio
"""

import asyncio
import sys
import struct
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Add the debabelizer module to the path
sys.path.append(str(Path("~/debabelizer").expanduser()))

from debabelizer.providers.stt.soniox import SonioxSTTProvider

def generate_speech_pattern_audio(duration_seconds=3.0, pattern="speech"):
    """Generate synthetic audio that mimics speech patterns"""
    sample_rate = 16000
    num_samples = int(sample_rate * duration_seconds)
    
    if pattern == "speech":
        # Generate speech-like audio with varying frequencies and pauses
        t = np.linspace(0, duration_seconds, num_samples, False)
        
        # Base frequency modulation (simulates speech)
        base_freq = 200 + 100 * np.sin(2 * np.pi * 0.5 * t)  # Slow pitch variation
        
        # Add formant-like frequencies
        formant1 = 0.3 * np.sin(2 * np.pi * 800 * t)
        formant2 = 0.2 * np.sin(2 * np.pi * 1200 * t)
        
        # Create speech envelope (with pauses)
        envelope = np.ones_like(t)
        # Add some pauses
        for pause_start in [0.8, 1.6, 2.4]:
            pause_end = pause_start + 0.2
            mask = (t >= pause_start) & (t < pause_end)
            envelope[mask] = 0.1
        
        # Combine all components
        audio = envelope * (
            0.4 * np.sin(2 * np.pi * base_freq * t) +
            formant1 + formant2 +
            0.1 * np.random.normal(0, 1, num_samples)  # Add some noise
        )
        
    elif pattern == "tones":
        # Generate tone patterns that might be interpreted as tonal languages
        t = np.linspace(0, duration_seconds, num_samples, False)
        frequencies = [262, 294, 330, 349, 392, 440, 494]  # C major scale
        
        audio = np.zeros(num_samples)
        segment_length = len(t) // len(frequencies)
        
        for i, freq in enumerate(frequencies):
            start_idx = i * segment_length
            end_idx = min((i + 1) * segment_length, len(t))
            segment_t = t[start_idx:end_idx] - t[start_idx]
            
            # Add frequency sweep within each tone
            freq_sweep = freq * (1 + 0.1 * np.sin(2 * np.pi * 2 * segment_t))
            audio[start_idx:end_idx] = 0.5 * np.sin(2 * np.pi * freq_sweep * segment_t)
    
    else:  # "noise"
        # Generate structured noise that might be interpreted as speech
        audio = 0.3 * np.random.normal(0, 1, num_samples)
        # Add some periodic components
        t = np.linspace(0, duration_seconds, num_samples, False)
        audio += 0.2 * np.sin(2 * np.pi * 150 * t)  # Low frequency component
    
    # Convert to 16-bit PCM
    audio = np.clip(audio, -1.0, 1.0)
    pcm_data = (audio * 32767).astype(np.int16)
    
    return struct.pack(f'{len(pcm_data)}h', *pcm_data)

async def test_soniox_language_detection():
    """Test Soniox language auto-detection with different audio patterns"""
    
    # Get API key from environment
    api_key = os.getenv("SONIOX_API_KEY")
    if not api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return
    
    print("🔊 Testing Soniox Language Auto-Detection")
    print("=" * 50)
    
    # Initialize Soniox provider
    provider = SonioxSTTProvider(api_key=api_key)
    
    # Test patterns that might trigger different language detection
    test_cases = [
        {
            "name": "Speech Pattern A (Low Pitch)",
            "audio_generator": lambda: generate_speech_pattern_audio(3.0, "speech"),
            "expected": "Might detect as Germanic/English"
        },
        {
            "name": "Tonal Pattern (High Pitch Variation)",
            "audio_generator": lambda: generate_speech_pattern_audio(3.0, "tones"),
            "expected": "Might detect as tonal language (Chinese/Vietnamese)"
        },
        {
            "name": "Structured Noise Pattern",
            "audio_generator": lambda: generate_speech_pattern_audio(3.0, "noise"),
            "expected": "Might trigger language detection algorithms"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"Expected: {test_case['expected']}")
        print("-" * 40)
        
        try:
            # Start streaming session with language auto-detection
            print("Starting Soniox streaming session...")
            session_id = await provider.start_streaming(
                language="auto",  # Enable auto-detection
                sample_rate=16000,
                audio_format="pcm",
                enable_dictation=True,
                include_nonfinal=True
            )
            print(f"✅ Session started: {session_id}")
            
            # Generate and stream audio
            print("Generating and streaming synthetic audio...")
            audio_data = test_case["audio_generator"]()
            
            # Stream audio in chunks (simulate real-time streaming)
            chunk_size = 1600  # 100ms chunks at 16kHz
            for offset in range(0, len(audio_data), chunk_size):
                chunk = audio_data[offset:offset + chunk_size]
                await provider.stream_audio(session_id, chunk)
                await asyncio.sleep(0.1)  # 100ms delay between chunks
            
            print("Audio streaming complete, waiting for results...")
            
            # Collect results
            results = []
            timeout_count = 0
            max_timeout = 30  # 3 seconds total wait
            
            async for result in provider.get_streaming_results(session_id):
                if result:
                    results.append(result)
                    print(f"📝 Result: '{result.text}' (final: {result.is_final})")
                    
                    # Check for language detection info
                    if hasattr(result, 'metadata') and result.metadata:
                        if 'language' in result.metadata:
                            print(f"🌐 Detected Language: {result.metadata['language']}")
                        if 'confidence' in result.metadata:
                            print(f"📊 Confidence: {result.metadata['confidence']}")
                    
                    if result.is_final:
                        break
                else:
                    timeout_count += 1
                    if timeout_count >= max_timeout:
                        print("⏰ Timeout waiting for results")
                        break
                    await asyncio.sleep(0.1)
            
            # Stop session
            await provider.stop_streaming(session_id)
            print(f"✅ Session stopped")
            
            # Summary
            if results:
                final_results = [r for r in results if r.is_final]
                if final_results:
                    print(f"📋 Final transcription: '{final_results[-1].text}'")
                else:
                    print("📋 No final transcription received")
            else:
                print("📋 No results received")
                
        except Exception as e:
            print(f"❌ Error in test {i}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 Language detection testing complete")

if __name__ == "__main__":
    import os
    asyncio.run(test_soniox_language_detection())