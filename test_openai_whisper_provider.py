#!/usr/bin/env python3
"""
Test the new OpenAI Whisper API provider in debabelizer
"""

import asyncio
import os
import sys
import struct
import numpy as np

# Add debabelizer to path
sys.path.append('/home/peter/debabelizer/src')

# Load environment variables
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

async def test_openai_whisper_provider():
    """Test the OpenAI Whisper provider implementation"""
    print("Testing OpenAI Whisper provider...")
    
    if not OPENAI_API_KEY:
        print("❌ No OpenAI API key found")
        return False
    
    try:
        # Import the provider
        from debabelizer.providers.stt.openai_whisper import OpenAIWhisperSTTProvider
        print("✅ OpenAI Whisper provider imported successfully")
        
        # Initialize provider
        provider = OpenAIWhisperSTTProvider(api_key=OPENAI_API_KEY)
        print("✅ Provider initialized")
        
        # Test connection
        print("🔄 Testing API connection...")
        connection_ok = await provider.test_connection()
        if connection_ok:
            print("✅ API connection successful")
        else:
            print("❌ API connection failed")
            return False
        
        # Test properties
        print(f"✅ Supports streaming: {provider.supports_streaming}")
        print(f"✅ Supports language detection: {provider.supports_language_detection}")
        print(f"✅ Supported languages: {len(provider.supported_languages)} languages")
        
        # Generate test speech-like audio
        print("🔄 Generating test audio...")
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create speech-like formants
        wave = (
            0.3 * np.sin(2 * np.pi * 300 * t) +  # Fundamental
            0.2 * np.sin(2 * np.pi * 900 * t) +  # First formant  
            0.1 * np.sin(2 * np.pi * 1500 * t)   # Second formant
        )
        
        # Add amplitude modulation
        modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 4 * t)
        wave = wave * modulation
        
        # Convert to PCM
        pcm_data = (wave * 16000).astype(np.int16)
        audio_bytes = struct.pack(f'<{len(pcm_data)}h', *pcm_data)
        
        print(f"✅ Generated {len(audio_bytes)} bytes of test audio")
        
        # Test transcription
        print("🔄 Testing audio transcription...")
        result = await provider.transcribe_audio(
            audio_data=audio_bytes,
            audio_format="wav",
            sample_rate=sample_rate,
            language="en"
        )
        
        print(f"✅ Transcription result:")
        print(f"   Text: '{result.text}'")
        print(f"   Confidence: {result.confidence}")
        print(f"   Language: {result.language_detected}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Words: {len(result.words)} word timings")
        print(f"   Metadata: {result.metadata}")
        
        # Test cost estimation
        cost = provider.get_cost_estimate(duration)
        print(f"✅ Estimated cost for {duration}s: ${cost:.4f}")
        
        # Test with different language
        print("🔄 Testing language detection...")
        result_auto = await provider.transcribe_audio(
            audio_data=audio_bytes,
            audio_format="wav", 
            sample_rate=sample_rate,
            language=None  # Auto-detect
        )
        
        print(f"✅ Auto-detection result: '{result_auto.text}' (lang: {result_auto.language_detected})")
        
        # Cleanup
        await provider.cleanup()
        print("✅ Provider cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing provider: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_whisper_provider())
    if success:
        print("\n✅ OpenAI Whisper provider test successful!")
        print("💡 Ready to integrate into debabelize.me backend")
    else:
        print("\n❌ OpenAI Whisper provider test failed!")