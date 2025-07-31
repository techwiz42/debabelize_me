#!/usr/bin/env python3
"""
Test Soniox language auto-detection with REAL human speech samples
"""

import asyncio
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Add the debabelizer module to the path
sys.path.append(str(Path("~/debabelizer").expanduser()))

from debabelizer.providers.stt.soniox import SonioxSTTProvider

def convert_mp3_to_pcm(mp3_file):
    """Convert MP3 file to 16kHz 16-bit mono PCM using ffmpeg"""
    try:
        # Create temporary PCM file
        with tempfile.NamedTemporaryFile(suffix='.pcm', delete=False) as temp_pcm:
            temp_pcm_path = temp_pcm.name
        
        # Use ffmpeg to convert MP3 to raw PCM
        cmd = [
            'ffmpeg', '-y',  # -y to overwrite output file
            '-i', str(mp3_file),  # Input MP3 file
            '-f', 's16le',  # Output as signed 16-bit little-endian
            '-ar', '16000',  # Sample rate 16kHz
            '-ac', '1',  # Mono channel
            temp_pcm_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            return None
        
        # Read the PCM data
        with open(temp_pcm_path, 'rb') as f:
            pcm_data = f.read()
        
        # Clean up temporary file
        os.unlink(temp_pcm_path)
        
        print(f"✅ Converted {mp3_file.name} to PCM ({len(pcm_data):,} bytes)")
        return pcm_data
        
    except Exception as e:
        print(f"❌ Error converting {mp3_file.name}: {e}")
        return None

async def test_language_detection_with_real_speech():
    """Test Soniox language auto-detection with real human speech"""
    
    # Get API key from environment
    api_key = os.getenv("SONIOX_API_KEY")
    if not api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return
    
    print("🎤 Testing Soniox Language Auto-Detection with REAL Human Speech")
    print("=" * 70)
    
    # Initialize Soniox provider
    provider = SonioxSTTProvider(api_key=api_key)
    
    # Test configurations with real human speech
    test_configs = [
        {
            "name": "English (British) - Auto-Detection",
            "file": "real_speech_english.mp3",
            "language": "auto",
            "expected_language": "en",
            "description": "Universal Declaration of Human Rights"
        },
        {
            "name": "Spanish - Auto-Detection", 
            "file": "real_speech_spanish.mp3",
            "language": "auto",
            "expected_language": "es",
            "description": "Universal Declaration of Human Rights"
        },
        {
            "name": "Chinese (Mandarin) - Auto-Detection",
            "file": "real_speech_chinese.mp3", 
            "language": "auto",
            "expected_language": "zh",
            "description": "Universal Declaration of Human Rights"
        },
        {
            "name": "Hindi - Auto-Detection",
            "file": "real_speech_hindi.mp3",
            "language": "auto",
            "expected_language": "hi",
            "description": "Universal Declaration of Human Rights"
        },
        # Test with explicit language specification for comparison
        {
            "name": "English (British) - Explicit Language",
            "file": "real_speech_english.mp3",
            "language": "en",
            "expected_language": "en",
            "description": "Universal Declaration of Human Rights"
        }
    ]
    
    audio_dir = Path("real_speech_samples")
    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        return
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🧪 Test {i}: {config['name']}")
        print(f"File: {config['file']}")
        print(f"Language Setting: {config['language']}")
        print(f"Expected Language: {config['expected_language']}")
        print("-" * 60)
        
        audio_file = audio_dir / config['file']
        if not audio_file.exists():
            print(f"❌ Audio file not found: {audio_file}")
            continue
        
        try:
            # Convert MP3 to PCM
            print("Converting real human speech MP3 to PCM...")
            pcm_data = convert_mp3_to_pcm(audio_file)
            if not pcm_data:
                print("❌ Failed to convert audio")
                continue
            
            # Start Soniox streaming session
            print(f"Starting Soniox session with language='{config['language']}'...")
            session_id = await provider.start_streaming(
                language=config['language'],
                sample_rate=16000,
                audio_format="pcm",
                include_nonfinal=True,
                enable_dictation=True
            )
            print(f"✅ Session started: {session_id}")
            
            # Stream PCM data in chunks (slower for real speech)
            print("Streaming real human speech data...")
            chunk_size = 3200  # 200ms chunks at 16kHz (2 bytes per sample)
            chunks_sent = 0
            
            for offset in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[offset:offset + chunk_size]
                await provider.stream_audio(session_id, chunk)
                chunks_sent += 1
                await asyncio.sleep(0.2)  # 200ms between chunks (realistic timing)
            
            print(f"Sent {chunks_sent} audio chunks of real human speech ({len(pcm_data):,} bytes total)")
            
            # Collect transcription results
            print("Collecting transcription results from real speech...")
            transcription_results = []
            timeout_count = 0
            max_timeout = 150  # 15 seconds total wait (more time for real speech)
            
            async for result in provider.get_streaming_results(session_id):
                if result:
                    transcription_results.append(result)
                    result_type = "FINAL" if result.is_final else "interim"
                    print(f"📝 {result_type}: '{result.text}'")
                    
                    # Check for language detection metadata
                    if hasattr(result, 'metadata') and result.metadata:
                        print(f"📋 Metadata: {result.metadata}")
                        if 'language' in result.metadata:
                            print(f"🌐 DETECTED LANGUAGE: {result.metadata['language']}")
                    
                    if result.is_final:
                        print("✅ Received final transcription from real speech")
                        break
                else:
                    timeout_count += 1
                    if timeout_count >= max_timeout:
                        print("⏰ Timeout waiting for results")
                        break
                    await asyncio.sleep(0.1)
            
            # Stop session
            await provider.stop_streaming(session_id)
            print("✅ Session stopped")
            
            # Analyze results
            test_result = {
                "config": config,
                "success": len(transcription_results) > 0,
                "results": transcription_results,
                "final_text": "",
                "detected_language": None,
                "language_detection_correct": False
            }
            
            if transcription_results:
                final_results = [r for r in transcription_results if r.is_final]
                if final_results:
                    test_result["final_text"] = final_results[-1].text
                
                # Check for language detection
                for result in transcription_results:
                    if hasattr(result, 'metadata') and result.metadata and 'language' in result.metadata:
                        test_result["detected_language"] = result.metadata['language']
                        test_result["language_detection_correct"] = (
                            result.metadata['language'] == config['expected_language']
                        )
                        break
            
            results.append(test_result)
            
            # Test summary
            print(f"\n📊 Test {i} Results:")
            print(f"  • Transcription Success: {'✅ Yes' if test_result['success'] else '❌ No'}")
            if test_result['final_text']:
                print(f"  • Final Text: '{test_result['final_text'][:100]}...'")
            else:
                print(f"  • Final Text: ❌ No transcription received")
            
            if test_result['detected_language']:
                detection_status = "✅ CORRECT" if test_result['language_detection_correct'] else "❌ INCORRECT"
                print(f"  • Language Detection: {detection_status}")
                print(f"    Detected: {test_result['detected_language']}")
                print(f"    Expected: {config['expected_language']}")
            else:
                print(f"  • Language Detection: ❌ NO DETECTION INFO")
                
        except Exception as e:
            print(f"❌ Error in test {i}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "config": config,
                "success": False,
                "error": str(e)
            })
    
    # Final comprehensive summary
    print("\n" + "=" * 70)
    print("🏁 COMPREHENSIVE LANGUAGE AUTO-DETECTION TEST RESULTS")
    print("=" * 70)
    
    successful_tests = [r for r in results if r.get('success', False)]
    auto_detection_tests = [r for r in successful_tests if r['config']['language'] == 'auto']
    correct_detections = [r for r in auto_detection_tests if r.get('language_detection_correct', False)]
    
    total_tests = len(results)
    auto_tests = len([r for r in results if r['config']['language'] == 'auto'])
    
    print(f"📊 OVERALL STATISTICS:")
    print(f"  • Total Tests: {total_tests}")
    print(f"  • Successful Transcriptions: {len(successful_tests)}/{total_tests} ({len(successful_tests)/total_tests*100:.1f}%)")
    print(f"  • Auto-Detection Tests: {auto_tests}")
    print(f"  • Successful Auto-Detection Tests: {len(auto_detection_tests)}/{auto_tests}")
    if auto_detection_tests:
        print(f"  • Correct Language Detection: {len(correct_detections)}/{len(auto_detection_tests)} ({len(correct_detections)/len(auto_detection_tests)*100:.1f}%)")
    
    if auto_detection_tests:
        print(f"\n🌐 AUTO-DETECTION DETAILED RESULTS:")
        for result in auto_detection_tests:
            config = result['config']
            detected = result.get('detected_language', 'None')
            expected = config['expected_language']
            status = "✅" if result.get('language_detection_correct', False) else "❌"
            
            # Extract language name from filename
            lang_name = config['file'].replace('real_speech_', '').replace('.mp3', '').title()
            print(f"  • {lang_name}: {status} Detected='{detected}' Expected='{expected}'")
    
    print(f"\n🎯 FINAL CONCLUSION:")
    if len(correct_detections) == auto_tests and auto_tests > 0:
        print(f"  ✅ SUCCESS: Soniox language auto-detection works perfectly!")
        print(f"     All {auto_tests} languages were correctly auto-detected.")
    elif len(correct_detections) > 0:
        print(f"  ⚠️  PARTIAL: Soniox auto-detection works for {len(correct_detections)}/{auto_tests} languages.")
        print(f"     Some languages were correctly detected, others were not.")
    elif len(auto_detection_tests) > 0:
        print(f"  ❌ FAILED: Soniox provided transcriptions but no language detection info.")
        print(f"     Speech recognition works, but auto-detection feature is not functioning.")
    else:
        print(f"  ❌ FAILED: Soniox could not transcribe any real human speech.")
        print(f"     Basic speech recognition is not working.")
    
    print(f"\n💡 RECOMMENDATION:")
    if len(correct_detections) >= 3:
        print(f"  ✅ Use Soniox with language='auto' for multi-language applications")
    elif len(successful_tests) >= 3:
        print(f"  ⚠️  Use Soniox with explicit language codes, auto-detection unreliable")
    else:
        print(f"  ❌ Consider alternative STT providers - Soniox integration issues")

if __name__ == "__main__":
    asyncio.run(test_language_detection_with_real_speech())