#!/usr/bin/env python3
"""
Test Google STT after gcloud authentication setup
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

async def test_google_stt_with_gcloud():
    """Test Google STT using gcloud authentication"""
    print("Testing Google STT with gcloud authentication...")
    
    # Check for gcloud credentials
    creds_path = os.path.expanduser('~/.config/gcloud/application_default_credentials.json')
    print(f"Looking for ADC at: {creds_path}")
    print(f"ADC file exists: {os.path.exists(creds_path)}")
    
    # Try importing Google Cloud libraries
    try:
        from google.cloud import speech_v1
        print("✅ Google Cloud Speech library available")
    except ImportError as e:
        print(f"❌ Google Cloud Speech library not available: {e}")
        return False
    
    try:
        import google.auth
        print("✅ Google auth library available")
    except ImportError as e:
        print(f"❌ Google auth library not available: {e}")
        return False
    
    # Test authentication
    print("\n🔄 Testing gcloud authentication...")
    try:
        credentials, project = google.auth.default()
        print(f"✅ Application Default Credentials found")
        print(f"   Project: {project}")
        print(f"   Credentials type: {type(credentials)}")
        
        # Test with debabelizer
        print("\n🔄 Testing debabelizer Google STT provider...")
        from debabelizer.providers.stt.google import GoogleSTTProvider
        
        # Initialize provider (should use ADC automatically)
        provider = GoogleSTTProvider()
        print("✅ GoogleSTTProvider initialized successfully")
        
        # Test connection
        connection_ok = await provider.test_connection()
        print(f"Connection test: {'✅ Successful' if connection_ok else '❌ Failed'}")
        
        if connection_ok:
            # Test actual transcription with synthetic audio
            print("\n🔄 Testing transcription with synthetic audio...")
            
            # Generate test audio (sine wave speech-like pattern)
            sample_rate = 16000
            duration = 2.0
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            # Create speech-like audio pattern
            wave = (
                0.3 * np.sin(2 * np.pi * 300 * t) +  # Fundamental (300Hz)
                0.2 * np.sin(2 * np.pi * 600 * t) +  # First harmonic
                0.1 * np.sin(2 * np.pi * 900 * t)    # Second harmonic
            )
            
            # Add speech-like envelope
            envelope = np.where(
                (t > 0.2) & (t < 0.8) | (t > 1.2) & (t < 1.8),
                0.8, 0.1
            )
            wave = wave * envelope
            
            # Convert to PCM bytes
            pcm_data = (wave * 16000).astype(np.int16)
            audio_bytes = struct.pack(f'<{len(pcm_data)}h', *pcm_data)
            
            print(f"Generated {len(audio_bytes)} bytes of test audio")
            
            # Test transcription
            try:
                result = await provider.transcribe_audio(
                    audio_data=audio_bytes,
                    audio_format="wav",
                    sample_rate=sample_rate,
                    language="en"
                )
                
                print("✅ Transcription successful!")
                print(f"   Text: '{result.text}'")
                print(f"   Confidence: {result.confidence}")
                print(f"   Duration: {result.duration:.2f}s")
                
                if result.words:
                    print(f"   Word count: {len(result.words)}")
                
                return True
                
            except Exception as e:
                print(f"❌ Transcription failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        return connection_ok
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_streaming_transcription():
    """Test streaming transcription if basic test passes"""
    print("\n🔄 Testing streaming transcription...")
    
    try:
        from debabelizer.providers.stt.google import GoogleSTTProvider
        
        provider = GoogleSTTProvider()
        
        # Start streaming session
        session_id = await provider.start_streaming(
            audio_format="wav",
            sample_rate=16000,
            language="en"
        )
        print(f"✅ Streaming session started: {session_id}")
        
        # Generate and stream audio chunks
        sample_rate = 16000
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(sample_rate * chunk_duration)
        
        # Stream for 2 seconds
        for i in range(20):
            # Generate chunk with varying frequency
            t = np.linspace(
                i * chunk_duration,
                (i + 1) * chunk_duration,
                chunk_samples,
                False
            )
            frequency = 300 + 100 * np.sin(i * 0.5)  # Varying frequency
            wave = 0.5 * np.sin(2 * np.pi * frequency * t)
            
            # Convert to PCM
            pcm_data = (wave * 16000).astype(np.int16)
            audio_chunk = struct.pack(f'<{len(pcm_data)}h', *pcm_data)
            
            # Send chunk
            await provider.stream_audio(session_id, audio_chunk)
            await asyncio.sleep(0.05)  # Small delay
        
        # Collect results
        results = []
        async for result in provider.get_streaming_results(session_id):
            results.append(result)
            print(f"   Stream result: '{result.text}' (final: {result.is_final})")
            
            # Break after a few results to avoid hanging
            if len(results) >= 5:
                break
        
        # Stop streaming
        await provider.stop_streaming(session_id)
        print(f"✅ Streaming session stopped, got {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Google STT Test with gcloud Authentication")
    print("=" * 60)
    
    success = asyncio.run(test_google_stt_with_gcloud())
    
    if success:
        print("\n✅ Basic Google STT test passed!")
        
        # Test streaming if basic test works
        streaming_success = asyncio.run(test_streaming_transcription())
        
        if streaming_success:
            print("\n🎉 All Google STT tests passed!")
            print("💡 Debabelizer Google STT provider is working correctly")
        else:
            print("\n⚠️  Basic transcription works, but streaming needs investigation")
    else:
        print("\n❌ Google STT test failed")
        print("💡 Run the following commands to set up authentication:")
        print("   gcloud auth login")
        print("   gcloud auth application-default login")
        print("   gcloud config set project YOUR_PROJECT_ID")