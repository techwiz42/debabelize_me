#!/usr/bin/env python3
"""
Simple verification that debabelizer's OpenAI Whisper provider works
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

async def test_openai_whisper_simple():
    """Simple test of OpenAI Whisper provider"""
    print("Testing OpenAI Whisper provider...")
    
    try:
        from debabelizer import VoiceProcessor
        print("✅ Debabelizer imported")
        
        # Create processor and force initialization
        print("🔄 Creating and initializing processor...")
        processor = VoiceProcessor(stt_provider="openai_whisper")
        
        # Generate simple test audio
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = 0.3 * np.sin(2 * np.pi * 440 * t)  # Simple 440Hz tone
        pcm_data = (wave * 16000).astype(np.int16)
        audio_bytes = struct.pack(f'<{len(pcm_data)}h', *pcm_data)
        
        print(f"✅ Generated {len(audio_bytes)} bytes of test audio")
        
        # Test transcription (this will initialize the provider)
        print("🔄 Testing transcription...")
        result = await processor.transcribe_audio(
            audio_data=audio_bytes,
            audio_format="wav",
            sample_rate=sample_rate,
            language="en"
        )
        
        print(f"✅ Transcription successful!")
        print(f"   Text: '{result.text}'")
        print(f"   Confidence: {result.confidence}")
        print(f"   Language: {result.language_detected}")
        print(f"   Processing time: {result.duration:.2f}s")
        print(f"   Provider model: {result.metadata.get('model', 'unknown')}")
        
        # Now check provider properties
        provider = processor.stt_provider
        if provider:
            print(f"✅ Provider loaded: {provider.name}")
            print(f"   Supports streaming: {provider.supports_streaming}")
            print(f"   Supports language detection: {provider.supports_language_detection}")
            print(f"   Languages supported: {len(provider.supported_languages)}")
        else:
            print("❌ Provider not loaded")
        
        # Test usage statistics
        stats = processor.get_usage_stats()
        print(f"✅ Usage stats: {stats['stt_requests']} requests, ${stats['cost_estimate']:.4f} estimated cost")
        
        # Cleanup
        await processor.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_whisper_simple())
    
    if success:
        print("\n✅ OpenAI Whisper provider works correctly!")
        print("💡 Ready for file-based transcription use cases")
        print("⚠️  Not suitable for real-time streaming")
    else:
        print("\n❌ OpenAI Whisper provider test failed!")