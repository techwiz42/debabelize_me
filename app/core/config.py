import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    debug: bool = False
    cors_origins: list[str] = [
        "http://localhost:3005", 
        "http://debabelize.me:3005", 
        "http://127.0.0.1:3005", 
        "http://0.0.0.0:3005",
        "https://debabelize.me"  # Production HTTPS
    ]
    
    # Google Search API
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    
    # Debabelizer provider settings
    deepgram_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    soniox_api_key: Optional[str] = None
    azure_speech_key: Optional[str] = None
    azure_speech_region: Optional[str] = None
    google_application_credentials: Optional[str] = None
    
    # Debabelizer preferences
    debabelizer_stt_provider: str = "whisper"  # Default to free local option
    debabelizer_tts_provider: str = "openai"   # Use OpenAI TTS if available
    debabelizer_optimize_for: str = "balanced"  # cost, latency, quality, balanced
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()