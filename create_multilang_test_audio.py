#!/usr/bin/env python3
"""
Create multi-language test audio files for Soniox language auto-detection testing
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the debabelizer module to the path
sys.path.append(str(Path("~/debabelizer").expanduser()))

from debabelizer import VoiceProcessor

# Test phrases in different languages
TEST_PHRASES = {
    "english": "Hello, this is a test of automatic language detection using Soniox streaming.",
    "spanish": "Hola, esta es una prueba de detección automática de idioma usando streaming de Soniox.",
    "french": "Bonjour, ceci est un test de détection automatique de langue en utilisant le streaming Soniox.",
    "german": "Hallo, dies ist ein Test der automatischen Spracherkennung mit Soniox-Streaming.",
    "italian": "Ciao, questo è un test di rilevamento automatico della lingua utilizzando lo streaming Soniox.",
    "portuguese": "Olá, este é um teste de detecção automática de idioma usando streaming Soniox.",
    "dutch": "Hallo, dit is een test van automatische taaldetectie met behulp van Soniox streaming.",
    "russian": "Привет, это тест автоматического определения языка с использованием потокового вещания Soniox.",
    "japanese": "こんにちは、これはSonioxストリーミングを使用した自動言語検出のテストです。",
    "chinese": "你好，这是使用Soniox流媒体进行自动语言检测的测试。"
}

async def create_multilang_audio_files():
    """Create TTS audio files in multiple languages"""
    
    # Initialize voice processor with ElevenLabs TTS
    voice_processor = VoiceProcessor()
    
    # Create output directory
    output_dir = Path("test_audio_files")
    output_dir.mkdir(exist_ok=True)
    
    print("Creating multi-language test audio files...")
    
    for language, phrase in TEST_PHRASES.items():
        try:
            print(f"Generating {language} audio: '{phrase[:50]}...'")
            
            # Generate TTS audio
            result = await voice_processor.synthesize(phrase)
            audio_data = result.audio_data
            
            # Save to file
            output_file = output_dir / f"test_{language}.mp3"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            print(f"✅ Created: {output_file}")
            
        except Exception as e:
            print(f"❌ Error creating {language} audio: {e}")
    
    print(f"\nAll audio files created in: {output_dir.absolute()}")
    return output_dir

if __name__ == "__main__":
    asyncio.run(create_multilang_audio_files())