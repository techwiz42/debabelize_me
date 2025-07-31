#!/usr/bin/env python3
"""
Test debabelizer with OpenAI Whisper provider
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

async def test_debabelizer_openai_whisper():
    """Test debabelizer VoiceProcessor with OpenAI Whisper"""
    print("Testing debabelizer with OpenAI Whisper provider...")
    
    try:
        from debabelizer import VoiceProcessor
        print("✅ Debabelizer imported successfully")
        
        # Initialize with OpenAI Whisper
        print("🔄 Creating VoiceProcessor with OpenAI Whisper...")
        processor = VoiceProcessor(stt_provider="openai_whisper")
        print("✅ VoiceProcessor created")
        
        # Check provider properties
        print(f"✅ STT Provider: {processor.stt_provider_name}")
        
        # Generate test audio
        print("🔄 Generating test audio...")
        sample_rate = 16000
        duration = 2.0  
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create speech-like audio with multiple harmonics
        wave = (
            0.4 * np.sin(2 * np.pi * 250 * t) +  # Fundamental
            0.3 * np.sin(2 * np.pi * 500 * t) +  # Second harmonic
            0.2 * np.sin(2 * np.pi * 750 * t) +  # Third harmonic
            0.1 * np.sin(2 * np.pi * 1000 * t)   # Fourth harmonic
        )
        
        # Add speech-like modulation
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)  # 3Hz envelope
        wave = wave * envelope
        
        # Convert to PCM
        pcm_data = (wave * 12000).astype(np.int16)
        audio_bytes = struct.pack(f'<{len(pcm_data)}h', *pcm_data)
        
        print(f"✅ Generated {len(audio_bytes)} bytes of test audio")
        
        # Test transcription
        print("🔄 Testing transcription with OpenAI Whisper...")
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
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Provider: {result.metadata.get('model', 'N/A')}")
        print(f"   Processing time: {result.metadata.get('processing_time', 'N/A'):.2f}s")
        
        # Test usage stats
        stats = processor.get_usage_stats()
        print(f"✅ Usage stats:")
        print(f"   STT requests: {stats['stt_requests']}")
        print(f"   Cost estimate: ${stats['cost_estimate']:.4f}")
        
        # Test provider connection
        print("🔄 Testing provider connectivity...")
        connection_tests = await processor.test_providers()
        for provider, status in connection_tests.items():
            print(f"   {provider}: {'✅' if status else '❌'}")
        
        # Test auto-detection
        print("🔄 Testing language auto-detection...")
        result_auto = await processor.transcribe_audio(
            audio_data=audio_bytes,
            audio_format="wav",
            sample_rate=sample_rate,
            language=None  # Auto-detect
        )
        
        print(f"✅ Auto-detection result: '{result_auto.text}' (detected: {result_auto.language_detected})")
        
        # Cleanup
        await processor.cleanup()
        print("✅ Processor cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_debabelizer_openai_whisper())
    if success:
        print("\n✅ Debabelizer OpenAI Whisper integration successful!")
        print("💡 Ready to create backend handler")
    else:
        print("\n❌ Debabelizer OpenAI Whisper test failed!")