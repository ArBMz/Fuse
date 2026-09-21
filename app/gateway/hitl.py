import uuid
import asyncio
from typing import Callable, Awaitable, Tuple
from app.config import settings

# The Deterministic Whitelist
# Any tool NOT in this list triggers the authorization pause.
SAFE_TOOLS = {
    "mouse_move",
    "mouse_click",
    "mouse_scroll",
    "type_text",
    "wait",
    "finish_task"
}

class HITLGateway:
    def __init__(self, send_event_callback: Callable[[str, dict], Awaitable[None]]):
        """
        Takes a callback function (from the WebSocket session) so it can 
        send payloads to the frontend without being tightly coupled to it.
        """
        self.send_event = send_event_callback
        
        # Async primitives to pause and resume the execution loop
        self.pending_auth_event = asyncio.Event()
        self.auth_decision = False
        self.current_action_id = None

    async def evaluate_action(self, tool_name: str, parameters: dict) -> Tuple[bool, str]:
        """
        Evaluates if an action is safe. If not, pauses execution and asks the frontend.
        Returns a tuple: (is_approved: bool, feedback_message: str)
        """
        
        # 1. Deterministic Safe Path
        if not settings.require_auth_for_all and tool_name in SAFE_TOOLS:
            return True, "Action approved by gateway whitelist."
            
        # 2. Unsafe Path: Pause and Ask User
        return await self._request_user_authorization(tool_name, parameters)

    async def _request_user_authorization(self, tool_name: str, parameters: dict) -> Tuple[bool, str]:
        """Halts the asyncio loop and pushes an auth request to the frontend."""
        
        # Generate a short, unique ID for this specific UI prompt
        self.current_action_id = f"req-{uuid.uuid4().hex[:8]}"
        
        # Reset the event lock and decision state
        self.pending_auth_event.clear()
        self.auth_decision = False
        
        print(f"[Gateway] Action trapped. Requesting user auth for: {tool_name}")
        
        # Push the interactive modal to the JS Chat UI
        await self.send_event("AUTH_REQUIRED", {
            "action_id": self.current_action_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "warning_message": f"The agent is attempting a restricted action: {tool_name}"
        })
        
        # =======================================================
        # THE FREEZE: Execution completely halts on this exact line
        # until self.pending_auth_event.set() is called.
        # =======================================================
        await self.pending_auth_event.wait()
        
        # Loop is unpaused. Process the user's decision.
        if self.auth_decision:
            print(f"[Gateway]  User approved: {tool_name}")
            return True, "User approved the action."
        else:
            print(f"[Gateway]  User denied: {tool_name}")
            return False, "User denied authorization for this action."

    async def resolve_auth(self, action_id: str, is_approved: bool):
        """
        Called by the WebSocket router when the user clicks Approve or Deny.
        This unblocks the paused execution loop.
        """
        # Validate that the UI is responding to the correct request
        if action_id == self.current_action_id:
            self.auth_decision = is_approved
            
            # This triggers the unfreeze for the pending_auth_event.wait() above
            self.pending_auth_event.set()
        else:
            print(f"[Gateway] Ignored auth response for mismatched action ID: {action_id}")