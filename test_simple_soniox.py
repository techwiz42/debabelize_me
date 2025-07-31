#!/usr/bin/env python3
"""
Simple test to check Soniox connection and see detailed logs
"""

import asyncio
import websockets
import json

WS_URL = "wss://debabelize.me/api/ws/stt"

async def test_simple_soniox():
    print("Testing simple Soniox connection with verbose logging...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"✅ Connected to {WS_URL}")
            
            # Send keepalive and wait for any initial responses
            await websocket.send(b'')
            print("✅ Sent keepalive")
            
            # Wait for responses for 10 seconds
            try:
                for i in range(10):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        try:
                            data = json.loads(message)
                            print(f"📨 RECEIVED: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError:
                            print(f"📨 RECEIVED (non-JSON): {message}")
                    except asyncio.TimeoutError:
                        print(f"⏱️ Waiting... ({i+1}/10)")
                        continue
                        
            except Exception as e:
                print(f"Error receiving: {e}")
                
            print("✅ Test complete")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 Testing simple Soniox connection...")
    asyncio.run(test_simple_soniox())