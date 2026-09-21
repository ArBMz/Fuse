import json
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config import settings
from app.agent.loop import AgentLoop

router = APIRouter()


class WebSocketSessionManager:
    """
    Manages the lifecycle of an active WebSocket connection,
    tracking the background execution task and bridging communication
    between the frontend and the agent.
    """
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.active_task: Optional[asyncio.Task] = None
        # Will hold reference to the agent instance once initialized
        self.agent = AgentLoop(websocket=self.websocket)

    async def send_event(self, event_type: str, payload: dict):
        """Standardized helper to send structured envelopes to client."""
        await self.websocket.send_json({
            "type": event_type,
            "payload": payload
        })

    async def start_task(self, prompt: str):
            """Cancels any ongoing execution and spawns a new agent run task."""
            await self.stop_task(reason="New task initiated by user.", notify=False)

            await self.send_event("STATUS_UPDATE", {
                "step_name": "init",
                "message": f"Starting task using {settings.ollama_model}..."
            })

            # Initialize the agent loop with the current WebSocket
            self.active_task = asyncio.create_task(self.agent.run(prompt))

    async def handle_auth_response(self, action_id: str, is_approved: bool):
        """Passes the authorization verdict to the agent gateway."""
        if self.agent and hasattr(self.agent, "gateway"):
            await self.agent.gateway.resolve_auth(action_id, is_approved)
        else:
            print(f"[WS Router] Received auth response for {action_id}, but no active agent exists.")

    async def stop_task(
        self,
        reason: str = "User initiated kill switch.",
        notify: bool = True,
    ):
        """Immediately halts the active background task and notifies the frontend."""
        if self.active_task and not self.active_task.done():
            self.active_task.cancel()
            try:
                await self.active_task
            except asyncio.CancelledError:
                pass
            self.active_task = None

        if self.agent and hasattr(self.agent, "stop"):
            await self.agent.stop()

        if notify:
            await self.send_event("TASK_COMPLETE", {
                "status": "aborted",
                "message": f"Execution halted: {reason}"
            })


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session = WebSocketSessionManager(websocket)
    print("[WS Router] Frontend client connected.")

    try:
        while True:
            raw_data = await websocket.receive_text()

            try:
                message = json.loads(raw_data)
            except json.JSONDecodeError:
                await session.send_event("STATUS_UPDATE", {
                    "step_name": "error",
                    "message": "Malformed JSON payload received."
                })
                continue

            msg_type = message.get("type")
            payload = message.get("payload", {})

            if msg_type == "START_TASK":
                prompt = payload.get("prompt", "").strip()
                if not prompt:
                    await session.send_event("STATUS_UPDATE", {
                        "step_name": "error",
                        "message": "Prompt cannot be empty."
                    })
                    continue
                print(f"[WS Router] Starting task: {prompt}")
                await session.start_task(prompt)

            elif msg_type == "AUTH_RESPONSE":
                action_id = payload.get("action_id")
                is_approved = bool(payload.get("is_approved", False))
                print(f"[WS Router] Authorization {action_id}: {'APPROVED' if is_approved else 'DENIED'}")
                await session.handle_auth_response(action_id, is_approved)

            elif msg_type == "KILL_SWITCH":
                reason = payload.get("reason", "Manual abort")
                print(f"[WS Router] KILL SWITCH triggered: {reason}")
                await session.stop_task(reason=reason)

            else:
                print(f"[WS Router] Unrecognized message type: {msg_type}")

    except WebSocketDisconnect:
        print("[WS Router] Frontend client disconnected. Cleaning up active tasks...")
        await session.stop_task(reason="Client disconnected.")