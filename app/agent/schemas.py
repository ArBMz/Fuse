# The master list of tools provided to the LLM on every inference request.
# Formatted to match Ollama/OpenAI strict tool-calling specifications.
OS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mouse_move",
            "description": "Moves the cursor to exact x, y screen coordinates. Always use this to hover over an element before clicking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "The X coordinate on the screen."},
                    "y": {"type": "integer", "description": "The Y coordinate on the screen."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Clicks the mouse button at the current cursor location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "button": {
                        "type": "string",
                        "enum": ["left", "right"],
                        "description": "The mouse button to click."
                    }
                },
                "required": ["button"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_scroll",
            "description": "Scrolls the mouse wheel up or down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clicks": {
                        "type": "integer",
                        "description": "Amount to scroll. Positive for up, negative for down."
                    }
                },
                "required": ["clicks"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Types a string of text. Use this to fill out forms or type commands. This does NOT press Enter. You must use press_key('enter') afterward if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The alphanumeric text to type."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Presses a specific system key (e.g., 'enter', 'tab', 'win', 'backspace').",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_name": {"type": "string", "description": "The name of the key to press."}
                },
                "required": ["key_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_hotkey",
            "description": "Executes a key combination sequentially.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keys to press together, e.g., ['ctrl', 'c']."
                    }
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Pauses execution. Use this immediately after clicking a button that loads a new page, or typing a command that takes time to execute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "description": "Number of seconds to wait. Usually 1.0 to 3.0."}
                },
                "required": ["seconds"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finish_task",
            "description": "Call this ONLY when the overarching user task is fully completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "A brief summary of what was accomplished."}
                },
                "required": ["message"]
            }
        }
    }
]

# The core persona and operating rules for the Vision Agent.
SYSTEM_PROMPT = """You are a highly capable autonomous computer use agent. 
You control a physical desktop environment through a strict set of tools.

Core Directives:
1. You will be provided with a screenshot of the current UI state. Analyze it carefully.
2. Only output ONE tool call at a time.
3. If you need to click something, you must FIRST call `mouse_move` to put the cursor on it, then `mouse_click` on the subsequent turn.
4. If you need to type into a field, you must FIRST move the mouse to it, click it, and then use `type_text`.
5. After actions that trigger UI changes (like pressing enter or clicking a link), call `wait` to allow the screen to update.
6. When the user's objective is achieved, call `finish_task`.
"""