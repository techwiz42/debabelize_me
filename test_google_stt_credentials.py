#!/usr/bin/env python3
"""
Test Google STT with existing credentials
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

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

async def test_google_stt_credentials():
    """Test what credentials we have for Google STT"""
    print("Testing Google STT credentials...")
    print(f"GOOGLE_API_KEY: {GOOGLE_API_KEY[:20]}..." if GOOGLE_API_KEY else "No GOOGLE_API_KEY found")
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')}")
    print(f"GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'Not set')}")
    
    # Try importing Google Cloud libraries
    try:
        from google.cloud import speech_v1
        print("✅ Google Cloud Speech library available")
    except ImportError as e:
        print(f"❌ Google Cloud Speech library not available: {e}")
        return False
    
    # Try importing Google auth
    try:
        import google.auth
        print("✅ Google auth library available")
    except ImportError as e:
        print(f"❌ Google auth library not available: {e}")
        return False
    
    # Test 1: Try with environment credentials (service account)
    print("\n🔄 Testing with environment credentials...")
    try:
        credentials, project = google.auth.default()
        print(f"✅ Default credentials found")
        print(f"   Project: {project}")
        print(f"   Credentials type: {type(credentials)}")
        
        # Try creating a client
        client = speech_v1.SpeechClient(credentials=credentials)
        print("✅ Speech client created with default credentials")
        
        return await test_google_stt_with_client(client)
        
    except Exception as e:
        print(f"❌ Default credentials failed: {e}")
    
    # Test 2: Try with API key (if possible)
    print("\n🔄 Testing with API key...")
    if GOOGLE_API_KEY:
        # Google Cloud Speech doesn't directly support API keys for authentication
        # It requires service account credentials or ADC (Application Default Credentials)
        print("⚠️  Google Cloud Speech-to-Text requires service account credentials")
        print("   Standard API keys are not supported for this service")
        print("   Need to set up service account and GOOGLE_APPLICATION_CREDENTIALS")
        return False
    else:
        print("❌ No Google API key found")
        return False

async def test_google_stt_with_client(client):
    """Test Google STT with an authenticated client"""
    print("\n🔄 Testing Google STT with authenticated client...")
    
    try:
        # Generate test audio
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create speech-like audio
        wave = (
            0.3 * np.sin(2 * np.pi * 300 * t) +  # Fundamental
            0.2 * np.sin(2 * np.pi * 600 * t) +  # First harmonic
            0.1 * np.sin(2 * np.pi * 900 * t)    # Second harmonic
        )
        
        # Add envelope
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)
        wave = wave * envelope
        
        # Convert to bytes
        pcm_data = (wave * 16000).astype(np.int16)
        audio_bytes = struct.pack(f'<{len(pcm_data)}h', *pcm_data)
        
        print(f"✅ Generated {len(audio_bytes)} bytes of test audio")
        
        # Test with Google Cloud Speech API
        from google.cloud.speech_v1 import enums
        
        config = speech_v1.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
            enable_automatic_punctuation=True
        )
        
        audio = speech_v1.RecognitionAudio(content=audio_bytes)
        
        print("🔄 Calling Google Speech API...")
        response = client.recognize(config=config, audio=audio)
        
        print("✅ Google Speech API call successful!")
        
        if response.results:
            for result in response.results:
                alternative = result.alternatives[0]
                print(f"   Transcription: '{alternative.transcript}'")
                print(f"   Confidence: {alternative.confidence}")
        else:
            print("   No transcription results (audio may be too simple)")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Speech API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_google_stt_credentials())
    
    if success:
        print("\n✅ Google STT credentials work!")
        print("💡 Can proceed with Google STT integration")
    else:
        print("\n❌ Google STT credentials not working")
        print("💡 Need to set up Google Cloud service account credentials")