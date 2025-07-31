#!/usr/bin/env python3
"""
Test Soniox language auto-detection support by examining API capabilities
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Add the debabelizer module to the path  
sys.path.append(str(Path("~/debabelizer").expanduser()))

from debabelizer.providers.stt.soniox import SonioxSTTProvider

async def test_soniox_language_support():
    """Test what language options Soniox supports"""
    
    # Get API key from environment
    api_key = os.getenv("SONIOX_API_KEY")
    if not api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return
    
    print("🌐 Testing Soniox Language Support")
    print("=" * 50)
    
    # Initialize Soniox provider
    provider = SonioxSTTProvider(api_key=api_key)
    
    # Test different language parameters
    language_tests = [
        {"name": "Auto-detection", "language": "auto"},
        {"name": "English", "language": "en"},
        {"name": "Spanish", "language": "es"},
        {"name": "French", "language": "fr"},
        {"name": "German", "language": "de"},
        {"name": "Italian", "language": "it"},
        {"name": "Portuguese", "language": "pt"},
        {"name": "Russian", "language": "ru"},
        {"name": "Japanese", "language": "ja"},
        {"name": "Chinese (Mandarin)", "language": "zh"},
        {"name": "Dutch", "language": "nl"},
        {"name": "Korean", "language": "ko"},
        {"name": "Arabic", "language": "ar"},
        {"name": "Hindi", "language": "hi"},
    ]
    
    supported_languages = []
    unsupported_languages = []
    
    for test in language_tests:
        print(f"\n🧪 Testing {test['name']} ('{test['language']}')")
        
        try:
            # Try to start a session with this language
            session_id = await provider.start_streaming(
                language=test['language'],
                sample_rate=16000,
                audio_format="pcm",
                include_nonfinal=True
            )
            
            print(f"✅ {test['name']} is supported")
            supported_languages.append(test)
            
            # Immediately stop the session
            await provider.stop_streaming(session_id)
            
        except Exception as e:
            print(f"❌ {test['name']} failed: {e}")
            unsupported_languages.append({"test": test, "error": str(e)})
    
    # Results summary
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    
    print(f"\n✅ SUPPORTED LANGUAGES ({len(supported_languages)}):")
    for lang in supported_languages:
        print(f"  • {lang['name']} ('{lang['language']}')")
    
    print(f"\n❌ UNSUPPORTED/FAILED LANGUAGES ({len(unsupported_languages)}):")
    for item in unsupported_languages:
        lang = item['test']
        error = item['error']
        print(f"  • {lang['name']} ('{lang['language']}') - {error[:100]}...")
    
    # Check specifically for auto-detection
    auto_detection_supported = any(lang['language'] == 'auto' for lang in supported_languages)
    
    print(f"\n🎯 LANGUAGE AUTO-DETECTION:")
    if auto_detection_supported:
        print("  ✅ Soniox supports language auto-detection (language='auto')")
        print("  📋 You can use language='auto' to enable automatic language detection")
    else:
        print("  ❌ Soniox does not support language auto-detection")
        print("  📋 You must specify a specific language code")
    
    print("\n" + "=" * 50)
    print("🏁 Language support testing complete")

if __name__ == "__main__":
    asyncio.run(test_soniox_language_support())