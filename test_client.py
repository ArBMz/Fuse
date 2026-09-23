import asyncio
import websockets
import json

async def test_agent():
    uri = "ws://127.0.0.1:8000/ws"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("🟢 Connected to Fuse Backend!")

            # 1. Start the task
            prompt = "click on the discord icon in the bottom of the screen on the toolbar and open the discord"
            start_msg = {
                "type": "START_TASK",
                "payload": {"prompt": prompt}
            }
            await websocket.send(json.dumps(start_msg))
            print(f"Sent Objective: '{prompt}'\n")
            print("Waiting for agent telemetry...\n" + "-"*40)

            # 2. Listen to the stream
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                msg_type = data.get("type")
                payload = data.get("payload", {})

                if msg_type == "STATUS_UPDATE":
                    step = payload.get("step_name", "").upper()
                    print(f"[{step}] {payload.get('message', '')}")
                    
                elif msg_type == "AGENT_MESSAGE":
                    print(f"\n🤖 FUSE SAYS: {payload.get('text', '')}\n")
                    
                elif msg_type == "AUTH_REQUIRED":
                    print(f"\n🛑 GATEWAY TRAP: Agent wants to use '{payload.get('tool_name')}'")
                    print(f"   Parameters: {payload.get('parameters')}")
                    
                    # Simulate human review time, then auto-approve
                    await asyncio.sleep(1)
                    print("   >> Auto-Approve injected by test script. <<")
                    
                    auth_reply = {
                        "type": "AUTH_RESPONSE",
                        "payload": {
                            "action_id": payload.get("action_id"),
                            "is_approved": True
                        }
                    }
                    await websocket.send(json.dumps(auth_reply))
                    
                elif msg_type == "TASK_COMPLETE":
                    print(f"\n🏁 TASK {payload.get('status').upper()}: {payload.get('message')}")
                    break
                    
                else:
                    print(f"[UNKNOWN ENVELOPE] {data}")

    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())