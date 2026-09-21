
import json
import asyncio
from fastapi import WebSocket

from app.os_env.vision import capture_screen_base64
import app.os_env.actuator as actuator
from app.agent.llm import get_next_action
from app.gateway.hitl import HITLGateway

class AgentLoop:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.is_running = False
        self.history = []
        
        # Initialize the gateway, passing our websocket sender function
        self.gateway = HITLGateway(self.send_event)

    async def send_event(self, event_type: str, payload: dict):
        """Helper to push standard envelopes over the WebSocket."""
        await self.websocket.send_json({
            "type": event_type,
            "payload": payload
        })

    async def stop(self):
        """Gracefully breaks the while loop."""
        self.is_running = False

    async def run(self, prompt: str):
        """The main continuous execution loop."""
        self.is_running = True
        
        # Add the initial user command to the conversation history
        self.history.append({"role": "user", "content": f"Objective: {prompt}"})
        
        try:
            while self.is_running:
                # 1. THE EYES: Capture the current screen
                await self.send_event("STATUS_UPDATE", {"step_name": "vision", "message": "Capturing screen state..."})
                image_base64 = capture_screen_base64(max_dimension=1200)
                
                # 2. THE BRAIN: Ask Ollama what to do next
                await self.send_event("STATUS_UPDATE", {"step_name": "inference", "message": "LLM is analyzing the screen..."})
                tool_call, text_content = await get_next_action(self.history, image_base64)
                
                # If the agent wants to speak to the user, push it to the UI
                if text_content:
                    await self.send_event("AGENT_MESSAGE", {"text": text_content})
                    self.history.append({"role": "assistant", "content": text_content})
                
                # 3. THE HANDS: Execute the requested tool
                if tool_call:
                    await self.handle_tool_call(tool_call)
                else:
                    # If the model didn't call a tool, we force it to try again
                    self.history.append({
                        "role": "user", 
                        "content": "You did not output a tool call. You must use a tool to accomplish the objective."
                    })
                    
                # Small pause to prevent rapid-fire loops that lock up the CPU
                await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            print("[Agent] Loop forcefully cancelled via Kill Switch.")
            raise  # Re-raise to let the router handle the cleanup
        except Exception as e:
            print(f"[Agent] Fatal error in execution loop: {e}")
            await self.send_event("TASK_COMPLETE", {"status": "error", "message": str(e)})

    async def handle_tool_call(self, tool_call: dict):
        """Extracts the tool, checks the gateway, and fires the OS actuator."""
        
        func_data = tool_call.get("function", {})
        tool_name = func_data.get("name")
        
        # Tool arguments usually come back as a JSON string
        raw_args = func_data.get("arguments", "{}")
        try:
            parameters = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            self.history.append({"role": "tool", "name": tool_name, "content": "Error: Invalid JSON arguments."})
            return

        # Record the agent's intent in the history
        self.history.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})

        # --- THE SECURITY GATEWAY ---
        await self.send_event("STATUS_UPDATE", {"step_name": "gateway", "message": f"Evaluating {tool_name}..."})
        is_approved, gateway_msg = await self.gateway.evaluate_action(tool_name, parameters)

        if not is_approved:
            # Feed the denial back into the history so the LLM knows it was blocked
            self.history.append({"role": "tool", "name": tool_name, "content": gateway_msg})
            return

        # --- THE ACTUATOR ---
        await self.send_event("STATUS_UPDATE", {"step_name": "executing", "message": f"Executing {tool_name}..."})
        try:
            # Dynamic Dispatch: Find the function in actuator.py matching 'tool_name'
            actuator_func = getattr(actuator, tool_name)
            result = actuator_func(**parameters)
            
            # Feed the success result back into the history
            self.history.append({"role": "tool", "name": tool_name, "content": result})
            
            # Check for terminal completion
            if tool_name == "finish_task":
                self.is_running = False
                await self.send_event("TASK_COMPLETE", {"status": "success", "message": result})
                
        except AttributeError:
            error_msg = f"Error: Tool '{tool_name}' does not exist."
            self.history.append({"role": "tool", "name": tool_name, "content": error_msg})
        except Exception as e:
            error_msg = f"Error executing tool: {str(e)}"
            self.history.append({"role": "tool", "name": tool_name, "content": error_msg})