#!/usr/bin/env python3
"""
Simple test to verify WebSocket connectivity and audio processing
"""

import asyncio
import websockets
import json
import struct
import numpy as np

async def test_simple_websocket():
    """Test basic WebSocket connection and audio sending"""
    
    print("🔌 Testing Basic WebSocket Connection")
    print("=" * 40)
    
    backend_ws_url = "wss://debabelize.me/api/ws/stt"
    
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect(backend_ws_url) as websocket:
            print("✅ Connected successfully")
            
            # Send a simple audio chunk (silence)
            print("Sending test audio chunk...")
            silence = struct.pack('<1600h', *([0] * 1600))  # 100ms of silence
            await websocket.send(silence)
            
            print("Waiting for any response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received within 5 seconds")
            
            print("✅ WebSocket test complete")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_websocket())