# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ollama Settings
    ollama_model: str = "qwen2.5-vl"
    ollama_host: str = "http://localhost:11434"
    
    # Screen Capture Settings
    use_multi_monitor: bool = False
    monitor_index: int = 1
    
    # Gateway Settings
    require_auth_for_all: bool = False

class Config:
        # Tells Pydantic to look for a .env file in the root directory
        env_file = ".env"
        # Ignores extra variables in the .env file that aren't defined here
        extra = "ignore"

# Instantiate the settings object to be imported across the app
settings = Settings()