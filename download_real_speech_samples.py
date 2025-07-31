#!/usr/bin/env python3
"""
Download real human speech samples from Omniglot for testing Soniox language auto-detection
"""

import asyncio
import aiohttp
import os
from pathlib import Path

# URLs for real human speech samples from Omniglot
SPEECH_SAMPLES = {
    "english": {
        "url": "https://omniglot.com/soundfiles/udhr/udhr_en.mp3",
        "description": "English (British) - Universal Declaration of Human Rights",
        "expected_language": "en"
    },
    "spanish": {
        "url": "https://omniglot.com/soundfiles/udhr/udhr_es.mp3", 
        "description": "Spanish - Universal Declaration of Human Rights",
        "expected_language": "es"
    },
    "chinese": {
        "url": "https://omniglot.com/soundfiles/udhr/udhr_mandarin.mp3",
        "description": "Chinese (Mandarin) - Universal Declaration of Human Rights", 
        "expected_language": "zh"
    },
    "hindi": {
        "url": "https://omniglot.com/soundfiles/udhr/udhr_hindi.mp3",
        "description": "Hindi - Universal Declaration of Human Rights",
        "expected_language": "hi"
    }
}

async def download_speech_sample(session, language, config, output_dir):
    """Download a single speech sample"""
    try:
        print(f"🔄 Downloading {language} sample...")
        print(f"   {config['description']}")
        
        async with session.get(config['url']) as response:
            if response.status == 200:
                audio_data = await response.read()
                
                # Save to file
                output_file = output_dir / f"real_speech_{language}.mp3"
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                
                print(f"✅ Downloaded: {output_file} ({len(audio_data):,} bytes)")
                return {
                    "language": language,
                    "file": output_file,
                    "size": len(audio_data),
                    "expected_language": config['expected_language'],
                    "description": config['description']
                }
            else:
                print(f"❌ Failed to download {language}: HTTP {response.status}")
                return None
                
    except Exception as e:
        print(f"❌ Error downloading {language}: {e}")
        return None

async def download_all_samples():
    """Download all speech samples"""
    
    print("🎤 Downloading Real Human Speech Samples")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("real_speech_samples")
    output_dir.mkdir(exist_ok=True)
    
    downloaded_samples = []
    
    async with aiohttp.ClientSession() as session:
        # Download all samples concurrently
        tasks = []
        for language, config in SPEECH_SAMPLES.items():
            task = download_speech_sample(session, language, config, output_dir)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Filter successful downloads
        downloaded_samples = [result for result in results if result is not None]
    
    # Summary
    print(f"\n📊 Download Summary:")
    print(f"Successfully downloaded: {len(downloaded_samples)}/{len(SPEECH_SAMPLES)} samples")
    print(f"Output directory: {output_dir.absolute()}")
    
    if downloaded_samples:
        print(f"\n📁 Downloaded Files:")
        for sample in downloaded_samples:
            print(f"  • {sample['language'].title()}: {sample['file'].name} ({sample['size']:,} bytes)")
            print(f"    {sample['description']}")
    
    return downloaded_samples

if __name__ == "__main__":
    asyncio.run(download_all_samples())