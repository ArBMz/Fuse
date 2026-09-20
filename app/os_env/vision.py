import base64
from io import BytesIO
import mss
from PIL import Image
from app.config import settings

def capture_screen_base64(max_dimension: int = 1200) -> str:
    """
    Captures the screen, scales it down to save VRAM, and returns a Base64 JPEG.
    """
    with mss.mss() as sct:
        # Determine which monitor to capture based on your .env settings
        # mss.monitors[0] is all monitors merged. mss.monitors[1] is the primary.
        if settings.use_multi_monitor and len(sct.monitors) > settings.monitor_index:
            monitor = sct.monitors[settings.monitor_index]
        else:
            monitor = sct.monitors[1] 
            
        # Grab the raw pixels
        sct_img = sct.grab(monitor)
        
        # Convert mss raw format to a Pillow Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        # Resize the image. thumbnail() maintains the aspect ratio.
        # This is critical for local LLMs to prevent Out-Of-Memory (OOM) errors.
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Convert to Base64 JPEG (JPEG is vastly smaller than PNG for this use case)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')