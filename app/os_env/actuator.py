import time
import pyautogui

# CRITICAL SECURITY FEATURE: 
# If the agent goes rogue, slam your physical mouse into any of the 4 corners 
# of your physical monitor. PyAutoGUI will instantly throw a FailSafeException and crash the loop.
pyautogui.FAILSAFE = True

def mouse_move(x: int, y: int) -> str:
    # Adding a slight duration makes the movement visible to the user
    # rather than instantly teleporting the cursor.
    pyautogui.moveTo(x, y, duration=0.2)
    return f"Success: Moved mouse to ({x}, {y})"

def mouse_click(button: str = "left") -> str:
    pyautogui.click(button=button)
    return f"Success: Clicked {button} mouse button"

def mouse_scroll(clicks: int) -> str:
    pyautogui.scroll(clicks)
    return f"Success: Scrolled {clicks} units"

def type_text(text: str) -> str:
    # interval=0.01 makes it type like a human, preventing UI buffers from dropping characters
    pyautogui.write(text, interval=0.01)
    return f"Success: Typed text '{text}'"

def press_key(key_name: str) -> str:
    pyautogui.press(key_name)
    return f"Success: Pressed key '{key_name}'"

def press_hotkey(keys: list) -> str:
    pyautogui.hotkey(*keys)
    return f"Success: Pressed hotkey combination {keys}"
    
def wait(seconds: float) -> str:
    time.sleep(seconds)
    return f"Success: Waited for {seconds} seconds"