import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Core API Keys
    openai_api_key: str
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    
    # Application Settings
    debug: bool = False
    environment: str = "development"
    
    # CORS Settings
    cors_origins: List[str] = [
        "http://localhost:3005", 
        "http://debabelize.me:3005", 
        "http://127.0.0.1:3005", 
        "http://0.0.0.0:3005",
        "https://debabelize.me"
    ]
    
    # Voice/Audio API Keys
    deepgram_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    soniox_api_key: Optional[str] = None
    azure_speech_key: Optional[str] = None
    azure_speech_region: Optional[str] = None
    google_application_credentials: Optional[str] = None
    
    # Debabelizer Settings
    debabelizer_stt_provider: str
    debabelizer_tts_provider: str
    debabelizer_optimize_for: str
    elevenlabs_output_format: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()