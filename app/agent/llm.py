import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.agent.schemas import OS_TOOLS, SYSTEM_PROMPT

async def get_next_action(
    conversation_history: List[Dict[str, Any]], 
    image_base64: str
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Sends the conversation history, the latest screen capture, and tool schemas to Ollama.
    Returns a tuple: (tool_call_dict, raw_text_response)
    """
    
    # 1. Initialize message list with the System Prompt if this is a fresh run
    messages = []
    if not conversation_history:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    
    # Append the running history (previous actions, user requests, tool results)
    messages.extend(conversation_history)

    # 2. Inject the current visual state
    # Ollama's API allows attaching an 'images' array directly to a standard message object.
    messages.append({
        "role": "user",
        "content": "This is the current screen state. Determine the next action and execute exactly ONE tool call.",
        "images": [image_base64]
    })

    # 3. Construct the exact JSON payload
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "tools": OS_TOOLS,
        "stream": False # We need the complete JSON response, not streaming text
    }

    try:
        # Increase timeout; local VLMs can take 5-15 seconds to process an image frame
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_host}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            message = data.get("message", {})
            
            # 4. Parse the LLM's decision
            tool_calls = message.get("tool_calls", [])
            raw_content = message.get("content", "")
            
            # The model successfully formatted a JSON tool execution
            if tool_calls:
                # We strictly enforce executing one step at a time
                return tool_calls[0], raw_content
                
            # The model failed to call a tool and just output standard text
            return None, raw_content

    except httpx.HTTPError as e:
        print(f"[LLM API] HTTP Connection Error with Ollama: {e}")
        return None, f"Connection error: {str(e)}"
    except Exception as e:
        print(f"[LLM API] Unexpected JSON parsing error: {e}")
        return None, f"Internal error: {str(e)}"