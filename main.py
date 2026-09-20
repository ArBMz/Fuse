import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import our validated settings
from app.config import settings

# We will build this router in the next step
from app.api.ws_router import router as websocket_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    print("========================================")
    print(f" Starting Fuse Vision Agent")
    print(f" Model: {settings.ollama_model}")
    print(f" Host:  {settings.ollama_host}")
    print(f" Auth:  {'Strict' if settings.require_auth_for_all else 'Standard Gateway'}")
    print("========================================")
    
    yield  # The application serves requests while yielded
    
    # --- Shutdown Logic ---
    print("🛑 Shutting down Fuse Vision Agent...")

# Initialize FastAPI with the lifespan manager
app = FastAPI(title="Fuse Vision Agent", lifespan=lifespan)

# Mount the static directory so FastAPI can serve the JS, CSS, and HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register the WebSocket router from the app/api module
app.include_router(websocket_router)

# Serve the main chat interface
@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    # Allows you to run the app by executing `python main.py` directly
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)