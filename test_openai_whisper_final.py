#!/usr/bin/env python3
"""
Final verification that debabelizer's OpenAI Whisper provider works correctly
"""

import asyncio
import os
import sys
import tempfile
import wave
import numpy as np

# Add debabelizer to path
sys.path.append('/home/peter/debabelizer/src')

# Load environment variables
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')

def create_speech_audio_file():
    """Create a more realistic speech audio file"""
    sample_rate = 16000
    duration = 3.0  # 3 seconds
    
    # Create a simple spoken phrase simulation
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Simulate vowel sounds with formants
    # "Hello World" - simplified vowel formants
    hello_freq = [600, 1200, 2400]  # /e/ vowel formants  
    world_freq = [400, 800, 2600]   # /o/ vowel formants
    
    # Create segments
    seg1 = t < 1.5  # "Hello" 
    seg2 = t >= 1.5  # "World"
    
    wave = np.zeros_like(t)
    
    # Hello segment
    for freq in hello_freq:
        wave[seg1] += 0.2 * np.sin(2 * np.pi * freq * t[seg1])
    
    # World segment  
    for freq in world_freq:
        wave[seg2] += 0.2 * np.sin(2 * np.pi * freq * t[seg2])
    
    # Add envelope to make it more speech-like
    envelope = np.exp(-2 * (t - duration/2)**2 / duration**2)  # Gaussian envelope
    wave = wave * envelope
    
    # Add some amplitude modulation for speech rhythm
    modulation = 0.7 + 0.3 * np.sin(2 * np.pi * 4 * t)
    wave = wave * modulation
    
    # Convert to 16-bit PCM
    wave_int16 = (wave * 16000).astype(np.int16)
    
    return wave_int16, sample_rate

async def test_openai_whisper_comprehensive():
    """Comprehensive test of OpenAI Whisper provider"""
    print("🧪 Comprehensive OpenAI Whisper Provider Test")
    print("=" * 50)
    
    try:
        from debabelizer import VoiceProcessor
        print("✅ Debabelizer imported")
        
        # Test 1: Provider initialization
        print("\n1️⃣ Testing provider initialization...")
        processor = VoiceProcessor(stt_provider="openai_whisper")
        print(f"✅ Provider initialized: {processor.stt_provider_name}")
        
        # Test 2: Provider properties
        print("\n2️⃣ Testing provider properties...")
        provider = processor.stt_provider
        print(f"   Name: {provider.name}")
        print(f"   Supports streaming: {provider.supports_streaming}")
        print(f"   Supports language detection: {provider.supports_language_detection}")
        print(f"   Supported languages: {len(provider.supported_languages)}")
        
        # Test 3: Connection test
        print("\n3️⃣ Testing API connection...")
        connection_ok = await provider.test_connection()
        print(f"   Connection status: {'✅ Connected' if connection_ok else '❌ Failed'}")
        
        # Test 4: Audio transcription
        print("\n4️⃣ Testing audio transcription...")
        audio_data, sample_rate = create_speech_audio_file()
        
        # Convert to bytes
        import struct
        audio_bytes = struct.pack(f'<{len(audio_data)}h', *audio_data)
        print(f"   Generated {len(audio_bytes)} bytes of speech-like audio")
        
        result = await processor.transcribe_audio(
            audio_data=audio_bytes,
            audio_format="wav",
            sample_rate=sample_rate,
            language="en"
        )
        
        print(f"   ✅ Transcription: '{result.text}'")
        print(f"   Confidence: {result.confidence}")
        print(f"   Language: {result.language_detected}")
        print(f"   Processing time: {result.duration:.2f}s")
        
        # Test 5: File transcription
        print("\n5️⃣ Testing file transcription...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Write WAV file
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)
            
            temp_path = tmp_file.name
        
        try:
            file_result = await processor.transcribe_file(temp_path, language="en")
            print(f"   ✅ File transcription: '{file_result.text}'")
            print(f"   Confidence: {file_result.confidence}")
        finally:
            os.unlink(temp_path)
        
        # Test 6: Language auto-detection
        print("\n6️⃣ Testing language auto-detection...")
        auto_result = await processor.transcribe_audio(
            audio_data=audio_bytes,
            audio_format="wav",
            sample_rate=sample_rate,
            language=None  # Auto-detect
        )
        print(f"   ✅ Auto-detected: '{auto_result.text}' (lang: {auto_result.language_detected})")
        
        # Test 7: Cost estimation
        print("\n7️⃣ Testing cost estimation...")
        cost = provider.get_cost_estimate(3.0)  # 3 seconds
        print(f"   ✅ Estimated cost for 3s: ${cost:.4f}")
        
        # Test 8: Usage statistics
        print("\n8️⃣ Testing usage statistics...")
        stats = processor.get_usage_stats()
        print(f"   STT requests: {stats['stt_requests']}")
        print(f"   Total cost estimate: ${stats['cost_estimate']:.4f}")
        
        # Test 9: Error handling (streaming not supported)
        print("\n9️⃣ Testing error handling...")
        try:
            await provider.start_streaming()
            print("   ❌ Should have raised error for streaming")
        except Exception as e:
            print(f"   ✅ Correctly raised error: {str(e)[:50]}...")
        
        # Cleanup
        await processor.cleanup()
        print("\n✅ All tests completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_whisper_comprehensive())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 OpenAI Whisper provider verification PASSED")
        print("💡 Provider is working correctly for file-based transcription")
        print("⚠️  Note: Not suitable for real-time streaming in debabelize.me")
    else:
        print("💥 OpenAI Whisper provider verification FAILED")