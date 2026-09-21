import time
import pyautogui
import mss

from app.config import settings

# CRITICAL SECURITY FEATURE: 
# If the agent goes rogue, slam your physical mouse into any of the 4 corners 
# of your physical monitor. PyAutoGUI will instantly throw a FailSafeException and crash the loop.
pyautogui.FAILSAFE = True


def _screen_coordinates_from_image(x: int, y: int, max_dimension: int = 1200) -> tuple[int, int]:
    """Convert coordinates from the resized model image to desktop coordinates."""
    with mss.mss() as sct:
        if settings.use_multi_monitor and len(sct.monitors) > settings.monitor_index:
            monitor = sct.monitors[settings.monitor_index]
        else:
            monitor = sct.monitors[1]

    scale = min(1.0, max_dimension / monitor["width"], max_dimension / monitor["height"])
    desktop_x = round(monitor["left"] + x / scale)
    desktop_y = round(monitor["top"] + y / scale)
    desktop_x = max(monitor["left"], min(desktop_x, monitor["left"] + monitor["width"] - 1))
    desktop_y = max(monitor["top"], min(desktop_y, monitor["top"] + monitor["height"] - 1))
    return desktop_x, desktop_y

def mouse_move(x: int, y: int) -> str:
    # Adding a slight duration makes the movement visible to the user
    # rather than instantly teleporting the cursor.
    desktop_x, desktop_y = _screen_coordinates_from_image(x, y)
    pyautogui.moveTo(desktop_x, desktop_y, duration=0.2)
    return f"Success: Moved mouse to ({desktop_x}, {desktop_y})"

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