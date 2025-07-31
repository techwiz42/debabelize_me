#!/usr/bin/env python3
"""
Test OpenAI's Whisper API using the API key from .env
This is different from the local Whisper models - uses cloud API instead
"""

import asyncio
import os
import struct
import numpy as np
import tempfile
from pathlib import Path

# Load environment variables
import sys
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def generate_test_audio():
    """Generate a simple test audio file"""
    sample_rate = 16000
    duration = 3.0  # 3 seconds
    frequency = 440  # A4 note
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    pcm_data = (wave * 32767).astype(np.int16)
    
    return pcm_data.tobytes(), sample_rate

async def test_openai_whisper_api():
    """Test OpenAI's cloud Whisper API"""
    print("Testing OpenAI Whisper API...")
    
    if not OPENAI_API_KEY:
        print("❌ No OpenAI API key found in backend/.env")
        return False
    
    print(f"✅ Found OpenAI API key: {OPENAI_API_KEY[:20]}...")
    
    try:
        # Try importing openai
        import openai
        print("✅ OpenAI library available")
        
        # Initialize client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized")
        
        # Generate test audio
        audio_data, sample_rate = generate_test_audio()
        print(f"✅ Generated {len(audio_data)} bytes of test audio at {sample_rate}Hz")
        
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Write WAV header
            import wave
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            temp_path = tmp_file.name
        
        print(f"✅ Saved test audio to: {temp_path}")
        
        try:
            # Test OpenAI Whisper API
            print("🔄 Calling OpenAI Whisper API...")
            
            with open(temp_path, 'rb') as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="json"
                )
            
            print(f"✅ OpenAI Whisper API Response:")
            print(f"   Text: '{transcription.text}'")
            print(f"   Duration: {getattr(transcription, 'duration', 'N/A')}")
            print(f"   Language: {getattr(transcription, 'language', 'N/A')}")
            
            # Test with verbose response
            print("\n🔄 Testing verbose response format...")
            with open(temp_path, 'rb') as audio_file:
                verbose_transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            
            print(f"✅ Verbose Response:")
            print(f"   Text: '{verbose_transcription.text}'")
            print(f"   Language: {verbose_transcription.language}")
            print(f"   Duration: {verbose_transcription.duration}")
            
            if hasattr(verbose_transcription, 'words') and verbose_transcription.words:
                print(f"   Words: {len(verbose_transcription.words)} word timestamps")
                for i, word in enumerate(verbose_transcription.words[:3]):  # Show first 3
                    print(f"     {i+1}. '{word.word}' ({word.start:.2f}s - {word.end:.2f}s)")
            
            return True
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
                print(f"🧹 Cleaned up temp file: {temp_path}")
            except:
                pass
        
    except ImportError:
        print("❌ OpenAI library not installed. Install with: pip install openai")
        return False
    except Exception as e:
        print(f"❌ Error testing OpenAI Whisper API: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_whisper_api())
    if success:
        print("\n✅ OpenAI Whisper API test successful!")
        print("💡 We can use OpenAI's cloud Whisper API instead of local models")
    else:
        print("\n❌ OpenAI Whisper API test failed!")