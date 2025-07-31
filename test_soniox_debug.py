#!/usr/bin/env python3
"""
Debug Soniox connection issues
"""

import asyncio
import json
import websockets

# Use the API key from the environment
SONIOX_API_KEY = "cfb7e338d94102d7b59deea599b238e4ae2fa8085830097c7e3ed89696c4ec95"

async def test_soniox_websocket():
    """Test raw Soniox WebSocket connection"""
    print("Testing raw Soniox WebSocket connection...")
    
    try:
        # Connect directly to Soniox WebSocket
        headers = {"Authorization": f"Bearer {SONIOX_API_KEY}"}
        
        print("Connecting to Soniox WebSocket...")
        async with websockets.connect(
            "wss://stt-rt.soniox.com/transcribe-websocket",
            additional_headers=headers,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=30
        ) as websocket:
            print("✅ Connected to Soniox WebSocket")
            
            # Send configuration
            config = {
                "api_key": SONIOX_API_KEY,
                "audio_format": "pcm_s16le",
                "sample_rate": 16000,
                "num_channels": 1,
                "model": "stt-rt-preview",
                "enable_language_identification": True,
                "include_nonfinal": True
            }
            
            print(f"Sending config: {config}")
            await websocket.send(json.dumps(config))
            
            # Wait for initial response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"✅ Got initial response: {data}")
                
                if "error" in data:
                    print(f"❌ Configuration error: {data['error']}")
                    return False
                    
            except asyncio.TimeoutError:
                print("⏱️ No initial response (timeout)")
                return False
            except Exception as e:
                print(f"❌ Error getting initial response: {e}")
                return False
            
            # Send a small test audio chunk (silence)
            test_audio = b'\x00' * 1024  # 1KB of silence
            print("Sending test audio...")
            await websocket.send(test_audio)
            
            # Listen for responses
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    print(f"📨 Response {i+1}: {data}")
                except asyncio.TimeoutError:
                    print(f"⏱️ Timeout waiting for response {i+1}")
                    continue
                except Exception as e:
                    print(f"❌ Error receiving response {i+1}: {e}")
                    break
            
            print("✅ Test completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_soniox_websocket())
    if success:
        print("✅ Soniox WebSocket test successful!")
    else:
        print("❌ Soniox WebSocket test failed!")