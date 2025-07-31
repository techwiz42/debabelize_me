#!/usr/bin/env python3
"""
Test OpenAI's Whisper API with speech-like audio
"""

import asyncio
import os
import struct
import numpy as np
import tempfile
import wave

# Load environment variables  
import sys
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def generate_speech_like_audio():
    """Generate more speech-like audio with varying frequencies"""
    sample_rate = 16000
    duration = 2.0  # 2 seconds
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create speech-like formants (multiple frequencies)  
    wave = (
        0.3 * np.sin(2 * np.pi * 200 * t) +  # Fundamental frequency
        0.2 * np.sin(2 * np.pi * 800 * t) +  # First formant
        0.1 * np.sin(2 * np.pi * 1200 * t)   # Second formant
    )
    
    # Add some amplitude modulation to simulate speech rhythm
    modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)  # 3Hz modulation
    wave = wave * modulation
    
    # Convert to 16-bit PCM
    pcm_data = (wave * 16000).astype(np.int16)
    
    return pcm_data.tobytes(), sample_rate

async def test_openai_whisper_simple():
    """Test OpenAI Whisper API with simpler parameters"""
    print("Testing OpenAI Whisper API (simplified)...")
    
    if not OPENAI_API_KEY:
        print("❌ No OpenAI API key found")
        return False
    
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Generate speech-like audio
        audio_data, sample_rate = generate_speech_like_audio()
        print(f"✅ Generated {len(audio_data)} bytes of speech-like audio")
        
        # Save to WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            temp_path = tmp_file.name
        
        try:
            # Test basic transcription
            print("🔄 Testing basic transcription...")
            with open(temp_path, 'rb') as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            print(f"✅ Basic transcription result: '{transcription.text}'")
            
            # Test with language specification
            print("🔄 Testing with language specification...")
            with open(temp_path, 'rb') as audio_file:
                transcription_en = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    language="en"
                )
            
            print(f"✅ English transcription: '{transcription_en.text}'")
            
            # Test JSON response format
            print("🔄 Testing JSON response format...")
            with open(temp_path, 'rb') as audio_file:
                transcription_json = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="json"
                )
            
            print(f"✅ JSON response: {transcription_json}")
            
            return True
            
        finally:
            os.unlink(temp_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_whisper_simple())
    if success:
        print("\n✅ OpenAI Whisper API working! Ready to integrate.")
    else:
        print("\n❌ OpenAI Whisper API test failed!")