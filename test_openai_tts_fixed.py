#!/usr/bin/env python3
"""
Test OpenAI TTS implementation fixes
"""

import asyncio
import os
import sys
import time

# Add debabelizer to path
sys.path.append('/home/peter/debabelizer/src')

# Load environment variables
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')

async def test_fixes():
    """Test the fixes made to OpenAI TTS"""
    print("Testing OpenAI TTS Fixes")
    print("=" * 40)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    from debabelizer.providers.tts.openai import OpenAITTSProvider
    provider = OpenAITTSProvider(api_key=api_key)
    
    # Test 1: Sample rate correction
    print("\n🔄 Testing sample rate correction...")
    result = await provider.synthesize(
        text="Testing sample rate accuracy.",
        voice_id="alloy"
    )
    
    print(f"✅ Sample rate fix:")
    print(f"   Reported sample rate: {result.sample_rate}")
    print(f"   Requested vs actual: {result.metadata.get('requested_sample_rate')} -> {result.metadata.get('actual_sample_rate')}")
    
    # Test 2: Duration estimation improvement
    print("\n🔄 Testing duration estimation improvement...")
    
    # Test with different text lengths
    test_texts = [
        "Short text.",
        "This is a medium length text that should provide better duration estimation.",
        "This is a much longer text that will help us test the accuracy of the new duration estimation algorithm which should be based on actual audio file size rather than just word count estimation which was quite inaccurate especially for longer texts."
    ]
    
    for i, text in enumerate(test_texts):
        result = await provider.synthesize(text=text, voice_id="alloy")
        estimation_method = result.metadata.get('duration_estimation_method', 'unknown')
        
        print(f"✅ Text {i+1} ({len(text)} chars):")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Estimation method: {estimation_method}")
        print(f"   Size: {result.size_bytes} bytes")
        print(f"   Rate: {result.size_bytes / result.duration:.0f} bytes/sec")
    
    # Test 3: Streaming improvements
    print("\n🔄 Testing streaming improvements...")
    
    # Capture log output to see warning
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    start_time = time.time()
    chunk_count = 0
    total_bytes = 0
    
    async for chunk in provider.synthesize_streaming(
        text="Testing improved streaming with better pacing and realistic delays.",
        voice_id="alloy"
    ):
        chunk_count += 1
        total_bytes += len(chunk)
        
        if chunk_count <= 3:  # Show timing for first few chunks
            elapsed = time.time() - start_time
            print(f"   Chunk {chunk_count}: {len(chunk)} bytes at {elapsed:.2f}s")
    
    total_time = time.time() - start_time
    print(f"✅ Streaming improvements:")
    print(f"   Total chunks: {chunk_count}")
    print(f"   Total bytes: {total_bytes}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average chunk time: {total_time / chunk_count:.3f}s")

if __name__ == "__main__":
    asyncio.run(test_fixes())