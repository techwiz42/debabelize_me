#!/usr/bin/env python3
"""
Test Soniox STT via backend WebSocket with real TTS audio samples
"""

import asyncio
import websockets
import json
import subprocess
import tempfile
import os
from pathlib import Path

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

async def test_language_via_backend():
    """Test multi-language STT via backend WebSocket"""
    
    print("🌐 Testing Multi-Language STT via Backend WebSocket")
    print("=" * 60)
    
    # Test configurations
    test_configs = [
        {
            "name": "English TTS → STT",
            "file": "speech_english.mp3",
            "expected_words": ["hello", "sarah", "testing", "speech", "recognition"]
        },
        {
            "name": "Spanish TTS → STT", 
            "file": "speech_spanish.mp3",
            "expected_words": ["hola", "carlos", "probando", "reconocimiento"]
        },
        {
            "name": "Chinese TTS → STT",
            "file": "speech_chinese.mp3", 
            "expected_words": ["你好", "李明", "测试", "语音", "识别"]
        },
        {
            "name": "Hindi TTS → STT",
            "file": "speech_hindi.mp3",
            "expected_words": ["नमस्ते", "राहुल", "परीक्षण", "प्रौद्योगिकी"]
        }
    ]
    
    audio_dir = Path("multilingual_speech_samples")
    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        return
    
    backend_ws_url = "wss://debabelize.me/api/ws/stt"
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🧪 Test {i}: {config['name']}")
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
            
            # Connect to backend WebSocket
            print("Connecting to backend WebSocket...")
            async with websockets.connect(backend_ws_url) as websocket:
                print("✅ Connected to backend")
                
                # Send PCM audio in chunks
                chunk_size = 1600  # 100ms chunks at 16kHz (2 bytes per sample)
                chunks_sent = 0
                
                print("Streaming audio chunks...")
                for offset in range(0, len(pcm_data), chunk_size):
                    chunk = pcm_data[offset:offset + chunk_size]
                    await websocket.send(chunk)
                    chunks_sent += 1
                    await asyncio.sleep(0.1)  # 100ms between chunks
                
                print(f"Sent {chunks_sent} audio chunks ({len(pcm_data):,} bytes total)")
                
                # Wait for transcription results
                print("Waiting for transcription results...")
                transcription_results = []
                timeout_count = 0
                max_timeout = 80  # 8 seconds
                
                while timeout_count < max_timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        
                        try:
                            data = json.loads(message)
                            transcription_results.append(data)
                            
                            result_type = "FINAL" if data.get('is_final', False) else "interim"
                            text = data.get('text', '')
                            print(f"📝 {result_type}: '{text}'")
                            
                            # Check for language detection
                            if 'language' in data:
                                print(f"🌐 Detected Language: {data['language']}")
                            if 'confidence' in data:
                                print(f"📊 Confidence: {data['confidence']}")
                            
                            if data.get('is_final', False):
                                print("✅ Received final transcription")
                                break
                                
                        except json.JSONDecodeError:
                            print(f"📨 Non-JSON message: {message}")
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        if timeout_count % 20 == 0:
                            print(f"⏳ Still waiting... ({timeout_count/10:.1f}s)")
                
                # Analyze results
                test_result = {
                    "config": config,
                    "success": len(transcription_results) > 0,
                    "results": transcription_results,
                    "final_text": "",
                    "detected_language": None,
                    "word_matches": 0
                }
                
                if transcription_results:
                    final_results = [r for r in transcription_results if r.get('is_final', False)]
                    if final_results:
                        test_result["final_text"] = final_results[-1].get('text', '')
                    
                    # Check for language detection
                    for result in transcription_results:
                        if 'language' in result:
                            test_result["detected_language"] = result['language']
                            break
                    
                    # Check word matches
                    final_text_lower = test_result["final_text"].lower()
                    for expected_word in config['expected_words']:
                        if expected_word.lower() in final_text_lower:
                            test_result["word_matches"] += 1
                
                results.append(test_result)
                
                # Test summary
                print(f"\n📊 Test {i} Results:")
                print(f"  • Success: {'✅ Yes' if test_result['success'] else '❌ No'}")
                if test_result['final_text']:
                    print(f"  • Transcription: '{test_result['final_text']}'")
                    accuracy = test_result['word_matches'] / len(config['expected_words']) * 100
                    print(f"  • Word Match Accuracy: {test_result['word_matches']}/{len(config['expected_words'])} ({accuracy:.1f}%)")
                else:
                    print(f"  • Transcription: ❌ No final result")
                
                if test_result['detected_language']:
                    print(f"  • Detected Language: {test_result['detected_language']}")
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
    
    if successful_tests:
        print(f"\n✅ SUCCESSFUL TRANSCRIPTIONS ({len(successful_tests)}):")
        for result in successful_tests:
            config = result['config']
            accuracy = result.get('word_matches', 0) / len(config['expected_words']) * 100
            print(f"  • {config['name']}: {accuracy:.1f}% word accuracy")
            print(f"    '{result.get('final_text', 'N/A')[:60]}...'")
    
    failed_tests = [r for r in results if not r.get('success', False)]
    if failed_tests:
        print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
        for result in failed_tests:
            config = result['config']
            error = result.get('error', 'No transcription received')
            print(f"  • {config['name']}: {error}")
    
    # Language detection summary
    lang_detections = [r.get('detected_language') for r in successful_tests if r.get('detected_language')]
    if lang_detections:
        print(f"\n🌐 Language Detection Results:")
        print(f"  • Languages detected: {', '.join(set(lang_detections))}")
        print(f"  • Detection rate: {len(lang_detections)}/{len(successful_tests)} ({len(lang_detections)/len(successful_tests)*100:.1f}%)")
    else:
        print(f"\n🌐 Language Detection: No language information received")
    
    print(f"\n💡 Test Conclusions:")
    if len(successful_tests) == total_tests:
        print(f"  ✅ Soniox STT successfully transcribed all {total_tests} languages")
    elif len(successful_tests) > 0:
        print(f"  ⚠️  Soniox STT transcribed {len(successful_tests)}/{total_tests} languages")
    else:
        print(f"  ❌ Soniox STT failed to transcribe any language")
    
    print(f"  📋 Recommendation: {'Use Soniox for multi-language STT' if len(successful_tests) >= 3 else 'Consider alternative STT providers'}")

if __name__ == "__main__":
    asyncio.run(test_language_via_backend())