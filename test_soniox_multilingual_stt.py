#!/usr/bin/env python3
"""
Test Soniox STT with real TTS audio samples in multiple languages
"""

import asyncio
import sys
import os
import struct
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import tempfile

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
        
        # Use ffmpeg to convert MP3 to PCM
        cmd = [
            'ffmpeg', '-y',  # -y to overwrite output file
            '-i', str(mp3_file),  # Input MP3 file
            '-f', 'wav',  # Output as WAV for easier processing
            '-ar', '16000',  # Sample rate 16kHz
            '-ac', '1',  # Mono channel
            '-acodec', 'pcm_s16le',  # 16-bit little-endian PCM
            temp_pcm_path.replace('.pcm', '.wav')
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            return None
        
        # Read the WAV file and extract PCM data (skip WAV header)
        wav_file = temp_pcm_path.replace('.pcm', '.wav')
        with open(wav_file, 'rb') as f:
            # Skip WAV header (typically 44 bytes)
            f.seek(44)
            pcm_data = f.read()
        
        # Clean up temporary files
        os.unlink(temp_pcm_path.replace('.pcm', '.wav'))
        if os.path.exists(temp_pcm_path):
            os.unlink(temp_pcm_path)
        
        print(f"✅ Converted {mp3_file.name} to PCM ({len(pcm_data):,} bytes)")
        return pcm_data
        
    except Exception as e:
        print(f"❌ Error converting {mp3_file.name}: {e}")
        return None

async def test_soniox_with_real_speech():
    """Test Soniox STT with real TTS audio in multiple languages"""
    
    # Get API key from environment
    api_key = os.getenv("SONIOX_API_KEY")
    if not api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return
    
    print("🎤 Testing Soniox STT with Real Multi-Language Speech")
    print("=" * 60)
    
    # Initialize Soniox provider
    provider = SonioxSTTProvider(api_key=api_key)
    
    # Test configurations
    test_configs = [
        {
            "name": "English with Auto-Detection",
            "file": "speech_english.mp3",
            "language": "auto",
            "expected_text": "Hello, my name is Sarah and I'm testing automatic speech recognition",
            "expected_lang": "en"
        },
        {
            "name": "Spanish with Auto-Detection", 
            "file": "speech_spanish.mp3",
            "language": "auto",
            "expected_text": "Hola, mi nombre es Carlos y estoy probando",
            "expected_lang": "es"
        },
        {
            "name": "Chinese with Auto-Detection",
            "file": "speech_chinese.mp3", 
            "language": "auto",
            "expected_text": "你好，我叫李明",
            "expected_lang": "zh"
        },
        {
            "name": "Hindi with Auto-Detection",
            "file": "speech_hindi.mp3",
            "language": "auto", 
            "expected_text": "नमस्ते, मेरा नाम राहुल है",
            "expected_lang": "hi"
        },
        # Test with explicit language specification
        {
            "name": "English with Explicit Language",
            "file": "speech_english.mp3",
            "language": "en",
            "expected_text": "Hello, my name is Sarah and I'm testing automatic speech recognition",
            "expected_lang": "en"
        },
        {
            "name": "Spanish with Explicit Language",
            "file": "speech_spanish.mp3", 
            "language": "es",
            "expected_text": "Hola, mi nombre es Carlos y estoy probando",
            "expected_lang": "es"
        }
    ]
    
    audio_dir = Path("multilingual_speech_samples")
    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        return
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🧪 Test {i}: {config['name']}")
        print(f"File: {config['file']}")
        print(f"Language: {config['language']}")
        print("-" * 50)
        
        audio_file = audio_dir / config['file']
        if not audio_file.exists():
            print(f"❌ Audio file not found: {audio_file}")
            continue
        
        try:
            # Convert MP3 to PCM
            print("Converting MP3 to PCM...")
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
            
            # Stream PCM data in chunks
            print("Streaming audio data...")
            chunk_size = 3200  # 200ms chunks at 16kHz (2 bytes per sample)
            chunks_sent = 0
            
            for offset in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[offset:offset + chunk_size]
                await provider.stream_audio(session_id, chunk)
                chunks_sent += 1
                await asyncio.sleep(0.2)  # 200ms between chunks
            
            print(f"Sent {chunks_sent} audio chunks ({len(pcm_data):,} bytes total)")
            
            # Collect transcription results
            print("Collecting transcription results...")
            transcription_results = []
            timeout_count = 0
            max_timeout = 100  # 10 seconds total wait
            
            async for result in provider.get_streaming_results(session_id):
                if result:
                    transcription_results.append(result)
                    result_type = "FINAL" if result.is_final else "interim"
                    print(f"📝 {result_type}: '{result.text}'")
                    
                    # Check for language detection metadata
                    if hasattr(result, 'metadata') and result.metadata:
                        print(f"📋 Metadata: {result.metadata}")
                    
                    if result.is_final:
                        print("✅ Received final transcription")
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
                "detected_language": None
            }
            
            if transcription_results:
                final_results = [r for r in transcription_results if r.is_final]
                if final_results:
                    test_result["final_text"] = final_results[-1].text
                
                # Check for language detection
                for result in transcription_results:
                    if hasattr(result, 'metadata') and result.metadata and 'language' in result.metadata:
                        test_result["detected_language"] = result.metadata['language']
                        break
            
            results.append(test_result)
            
            # Test summary
            print(f"\n📊 Test {i} Results:")
            print(f"  • Success: {'✅ Yes' if test_result['success'] else '❌ No'}")
            if test_result['final_text']:
                print(f"  • Transcription: '{test_result['final_text']}'")
                # Check accuracy
                expected_start = config['expected_text'].lower()
                actual_text = test_result['final_text'].lower()
                if expected_start in actual_text or actual_text.startswith(expected_start[:20]):
                    print(f"  • Accuracy: ✅ Good match")
                else:
                    print(f"  • Accuracy: ⚠️  Partial/No match")
            else:
                print(f"  • Transcription: ❌ No final result")
            
            if test_result['detected_language']:
                print(f"  • Detected Language: {test_result['detected_language']}")
                if test_result['detected_language'] == config['expected_lang']:
                    print(f"  • Language Detection: ✅ Correct")
                else:
                    print(f"  • Language Detection: ⚠️  Expected {config['expected_lang']}")
            else:
                print(f"  • Language Detection: ❌ No language info")
                
        except Exception as e:
            print(f"❌ Error in test {i}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "config": config,
                "success": False,
                "error": str(e)
            })
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results if r.get('success', False)]
    total_tests = len(results)
    
    print(f"Overall Success Rate: {len(successful_tests)}/{total_tests} ({len(successful_tests)/total_tests*100:.1f}%)")
    
    print(f"\n✅ SUCCESSFUL TESTS ({len(successful_tests)}):")
    for result in successful_tests:
        config = result['config']
        print(f"  • {config['name']}: '{result.get('final_text', 'N/A')[:50]}...'")
    
    failed_tests = [r for r in results if not r.get('success', False)]
    if failed_tests:
        print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
        for result in failed_tests:
            config = result['config']
            error = result.get('error', 'No transcription received')
            print(f"  • {config['name']}: {error}")
    
    print(f"\n💡 Language Auto-Detection Results:")
    auto_detection_tests = [r for r in successful_tests if r['config']['language'] == 'auto']
    if auto_detection_tests:
        correct_detections = 0
        for result in auto_detection_tests:
            detected = result.get('detected_language')
            expected = result['config']['expected_lang']
            if detected == expected:
                correct_detections += 1
        
        print(f"  • Auto-detection accuracy: {correct_detections}/{len(auto_detection_tests)} ({correct_detections/len(auto_detection_tests)*100:.1f}%)")
    else:
        print(f"  • No successful auto-detection tests")

if __name__ == "__main__":
    asyncio.run(test_soniox_with_real_speech())