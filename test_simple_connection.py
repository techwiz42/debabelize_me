#!/usr/bin/env python3
"""
Simple connection test without sending audio
"""

import asyncio
import websockets
import json

WS_URL = "wss://debabelize.me/api/ws/stt"

async def test_simple():
    print("Testing simple WebSocket connection...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"✅ Connected to {WS_URL}")
            
            # Just send keepalive and wait
            await websocket.send(b'')
            print("✅ Sent keepalive")
            
            # Wait for any responses for 5 seconds
            try:
                for i in range(5):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        print(f"📨 RECEIVED: {json.dumps(data, indent=2)}")
                    except asyncio.TimeoutError:
                        print(f"⏱️ Waiting... ({i+1}/5)")
                        continue
                        
            except Exception as e:
                print(f"Error receiving: {e}")
                
            print("✅ Test complete")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())