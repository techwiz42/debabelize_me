#!/usr/bin/env python3
"""
Generate real TTS audio samples in multiple languages for Soniox STT testing
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Add the debabelizer module to the path
sys.path.append(str(Path("~/debabelizer").expanduser()))

from debabelizer import VoiceProcessor

# Test phrases in different languages (5-10 seconds when spoken)
TEST_PHRASES = {
    "english": {
        "text": "Hello, my name is Sarah and I'm testing automatic speech recognition technology. This system should be able to detect that I'm speaking English and transcribe my words accurately. The weather is beautiful today and I hope this test works perfectly.",
        "language": "en"
    },
    "spanish": {
        "text": "Hola, mi nombre es Carlos y estoy probando la tecnología de reconocimiento automático de voz. Este sistema debería poder detectar que estoy hablando en español y transcribir mis palabras con precisión. El clima está hermoso hoy y espero que esta prueba funcione perfectamente.",
        "language": "es"
    },
    "chinese": {
        "text": "你好，我叫李明，我正在测试自动语音识别技术。这个系统应该能够检测到我在说中文，并准确转录我的话。今天天气很好，我希望这个测试能完美运行。人工智能技术真的很神奇。",
        "language": "zh"
    },
    "hindi": {
        "text": "नमस्ते, मेरा नाम राहुल है और मैं स्वचालित वाक् पहचान प्रौद्योगिकी का परीक्षण कर रहा हूं। इस सिस्टम को यह पता लगाना चाहिए कि मैं हिंदी में बोल रहा हूं और मेरे शब्दों को सटीक रूप से लिखना चाहिए। आज मौसम बहुत अच्छा है और मुझे उम्मीद है कि यह परीक्षण पूरी तरह से काम करेगा।",
        "language": "hi"
    }
}

async def generate_multilingual_audio():
    """Generate TTS audio files in multiple languages"""
    
    print("🎤 Generating Multi-Language Speech Samples")
    print("=" * 50)
    
    # Initialize voice processor with ElevenLabs TTS
    voice_processor = VoiceProcessor()
    
    # Create output directory
    output_dir = Path("multilingual_speech_samples")
    output_dir.mkdir(exist_ok=True)
    
    generated_files = {}
    
    for language_name, config in TEST_PHRASES.items():
        try:
            print(f"\n🗣️  Generating {language_name.title()} speech...")
            print(f"Text: {config['text'][:60]}...")
            
            # Generate TTS audio
            result = await voice_processor.synthesize(
                text=config['text'],
                language=config['language']
            )
            
            # Save to file
            output_file = output_dir / f"speech_{language_name}.mp3"
            with open(output_file, "wb") as f:
                f.write(result.audio_data)
            
            generated_files[language_name] = {
                "file": output_file,
                "text": config['text'],
                "language": config['language'],
                "size_bytes": len(result.audio_data)
            }
            
            print(f"✅ Generated: {output_file} ({len(result.audio_data):,} bytes)")
            
        except Exception as e:
            print(f"❌ Error generating {language_name} audio: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n📊 Generation Complete!")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Generated {len(generated_files)} audio files:")
    
    for lang, info in generated_files.items():
        print(f"  • {lang.title()}: {info['file'].name} ({info['size_bytes']:,} bytes)")
    
    return generated_files

if __name__ == "__main__":
    asyncio.run(generate_multilingual_audio())