#!/usr/bin/env python3
"""
Test OpenAI TTS implementation in debabelizer
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add debabelizer to path
sys.path.append('/home/peter/debabelizer/src')

# Load environment variables
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')

async def test_openai_tts():
    """Test OpenAI TTS implementation"""
    print("=" * 60)
    print("OpenAI TTS Test")
    print("=" * 60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"OPENAI_API_KEY: {api_key[:20]}..." if api_key else "No OPENAI_API_KEY found")
    
    if not api_key:
        print("❌ No OpenAI API key found")
        return False
    
    # Test 1: Import and initialization
    print("\n🔄 Testing OpenAI TTS provider import and initialization...")
    try:
        from debabelizer.providers.tts.openai import OpenAITTSProvider
        print("✅ OpenAI TTS provider imported successfully")
        
        provider = OpenAITTSProvider(api_key=api_key)
        print("✅ OpenAI TTS provider initialized")
        print(f"   Default model: {provider.default_model}")
        print(f"   Default voice: {provider.default_voice}")
        print(f"   Supported languages: {len(provider.supported_languages)}")
        print(f"   Supports streaming: {provider.supports_streaming}")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Test 2: Check required dependencies
    print("\n🔄 Testing OpenAI library dependency...")
    try:
        from openai import AsyncOpenAI
        print("✅ OpenAI library available")
        
        # Check version
        try:
            import openai
            version = getattr(openai, '__version__', 'unknown')
            print(f"   Version: {version}")
        except:
            print("   Version: unknown")
            
    except ImportError:
        print("❌ OpenAI library not installed")
        print("💡 Install with: pip install openai>=1.0.0")
        return False
    
    # Test 3: Get available voices
    print("\n🔄 Testing available voices...")
    try:
        voices = await provider.get_available_voices()
        print(f"✅ Retrieved {len(voices)} voices:")
        for voice in voices:
            print(f"   - {voice.voice_id}: {voice.name} ({voice.gender}, {voice.language})")
            print(f"     {voice.description}")
            
    except Exception as e:
        print(f"❌ Failed to get voices: {e}")
        return False
    
    # Test 4: Connection test
    print("\n🔄 Testing API connection...")
    try:
        connection_ok = await provider.test_connection()
        if connection_ok:
            print("✅ API connection successful")
        else:
            print("❌ API connection failed")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    # Test 5: Basic synthesis
    print("\n🔄 Testing basic text synthesis...")
    test_text = "Hello, this is a test of OpenAI's text-to-speech synthesis."
    try:
        start_time = time.time()
        result = await provider.synthesize(
            text=test_text,
            voice_id="alloy",
            audio_format=None  # Use default
        )
        synthesis_time = time.time() - start_time
        
        print("✅ Basic synthesis successful!")
        print(f"   Text: '{test_text}'")
        print(f"   Voice used: {result.voice_used.voice_id} ({result.voice_used.name})")
        print(f"   Audio format: {result.format}")
        print(f"   Sample rate: {result.sample_rate}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Size: {result.size_bytes} bytes")
        print(f"   Synthesis time: {synthesis_time:.2f}s")
        print(f"   Character count: {result.metadata.get('character_count', 'unknown')}")
        print(f"   Word count: {result.metadata.get('word_count', 'unknown')}")
        print(f"   Model: {result.metadata.get('model', 'unknown')}")
        
        # Save audio file for verification
        output_path = Path("test_openai_tts_output.mp3")
        with open(output_path, "wb") as f:
            f.write(result.audio_data)
        print(f"   Audio saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Basic synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Different voices
    print("\n🔄 Testing different voices...")
    test_voices = ["echo", "fable", "nova", "shimmer"]
    for voice_id in test_voices:
        try:
            result = await provider.synthesize(
                text=f"This is the {voice_id} voice speaking.",
                voice_id=voice_id
            )
            print(f"✅ Voice '{voice_id}': {result.size_bytes} bytes, {result.duration:.2f}s")
        except Exception as e:
            print(f"❌ Voice '{voice_id}' failed: {e}")
    
    # Test 7: Different models
    print("\n🔄 Testing different models...")
    test_models = ["tts-1", "tts-1-hd"]
    for model in test_models:
        try:
            start_time = time.time()
            result = await provider.synthesize(
                text="Testing different TTS models for quality comparison.",
                voice_id="alloy",
                model=model
            )
            synthesis_time = time.time() - start_time
            print(f"✅ Model '{model}': {result.size_bytes} bytes, {synthesis_time:.2f}s synthesis time")
        except Exception as e:
            print(f"❌ Model '{model}' failed: {e}")
    
    # Test 8: Speed variations
    print("\n🔄 Testing speed variations...")
    test_speeds = [0.5, 1.0, 1.5, 2.0]
    for speed in test_speeds:
        try:
            result = await provider.synthesize(
                text="Testing speech speed variations from slow to fast.",
                voice_id="alloy",
                speed=speed
            )
            print(f"✅ Speed {speed}x: {result.duration:.2f}s duration, {result.size_bytes} bytes")
        except Exception as e:
            print(f"❌ Speed {speed}x failed: {e}")
    
    # Test 9: Long text handling
    print("\n🔄 Testing long text handling...")
    # Generate text near the 4096 character limit
    long_text = "This is a test of long text synthesis. " * 100  # ~3900 chars
    try:
        result = await provider.synthesize(
            text=long_text,
            voice_id="alloy"
        )
        print(f"✅ Long text ({len(long_text)} chars): {result.duration:.2f}s, {result.size_bytes} bytes")
    except Exception as e:
        print(f"❌ Long text failed: {e}")
    
    # Test 10: Text length validation
    print("\n🔄 Testing text length validation...")
    try:
        very_long_text = "X" * 5000  # Over 4096 limit
        result = await provider.synthesize(
            text=very_long_text,
            voice_id="alloy"
        )
        print("❌ Should have failed for text > 4096 characters")
    except Exception as e:
        if "too long" in str(e).lower() or "4096" in str(e):
            print("✅ Text length validation working correctly")
        else:
            print(f"❌ Unexpected error for long text: {e}")
    
    # Test 11: Streaming synthesis
    print("\n🔄 Testing streaming synthesis...")
    try:
        chunks = []
        chunk_count = 0
        start_time = time.time()
        
        async for chunk in provider.synthesize_streaming(
            text="This is a test of streaming synthesis functionality.",
            voice_id="alloy"
        ):
            chunks.append(chunk)
            chunk_count += 1
            
        streaming_time = time.time() - start_time
        total_bytes = sum(len(chunk) for chunk in chunks)
        
        print(f"✅ Streaming synthesis completed:")
        print(f"   Chunks received: {chunk_count}")
        print(f"   Total bytes: {total_bytes}")
        print(f"   Streaming time: {streaming_time:.2f}s")
        print(f"   Average chunk size: {total_bytes // chunk_count if chunk_count > 0 else 0} bytes")
        
        # Save streaming result
        streaming_path = Path("test_openai_tts_streaming.mp3")
        with open(streaming_path, "wb") as f:
            for chunk in chunks:
                f.write(chunk)
        print(f"   Streaming audio saved to: {streaming_path}")
        
    except Exception as e:
        print(f"❌ Streaming synthesis failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 12: Cost estimation
    print("\n🔄 Testing cost estimation...")
    try:
        short_cost = provider.get_cost_estimate("Short text")
        long_cost = provider.get_cost_estimate("X" * 1000)  # 1000 chars
        
        print(f"✅ Cost estimation working:")
        print(f"   Short text (~10 chars): ${short_cost:.6f}")
        print(f"   1000 characters: ${long_cost:.6f}")
        print(f"   Cost per 1000 chars: ${provider.get_cost_estimate('X' * 1000):.6f}")
        
    except Exception as e:
        print(f"❌ Cost estimation failed: {e}")
    
    # Test 13: Error handling
    print("\n🔄 Testing error handling...")
    
    # Test invalid voice
    try:
        await provider.synthesize(text="Test", voice_id="invalid_voice")
        print("❌ Should have failed for invalid voice")
    except Exception as e:
        if "not found" in str(e).lower():
            print("✅ Invalid voice error handling working")
        else:
            print(f"❌ Unexpected error for invalid voice: {e}")
    
    # Test empty text
    try:
        await provider.synthesize(text="")
        print("❌ Should have failed for empty text")
    except Exception as e:
        print(f"✅ Empty text handled: {e}")
    
    print("\n" + "=" * 60)
    print("✅ OpenAI TTS test completed!")
    print("💡 Check generated audio files:")
    print("   - test_openai_tts_output.mp3")
    print("   - test_openai_tts_streaming.mp3")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_openai_tts())
    
    if success:
        print("\n🎉 OpenAI TTS implementation appears to be working!")
    else:
        print("\n❌ OpenAI TTS implementation has issues that need to be addressed.")