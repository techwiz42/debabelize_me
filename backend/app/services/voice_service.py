from debabelizer import VoiceProcessor, DebabelizerConfig
from app.core.config import settings
import traceback

class VoiceService:
    def __init__(self):
        self.stt_processor = None
        self.tts_processor = None
        self._config = self._create_debabelizer_config()
    
    def _create_debabelizer_config(self):
        """Create DebabelizerConfig with API keys for all supported STT and TTS providers"""
        config_dict = {}
        
        # STT Providers
        if hasattr(settings, 'deepgram_api_key') and settings.deepgram_api_key:
            config_dict['deepgram'] = {'api_key': settings.deepgram_api_key}
        
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            config_dict['openai'] = {'api_key': settings.openai_api_key}
        
        if hasattr(settings, 'azure_speech_key') and settings.azure_speech_key:
            config_dict['azure'] = {'api_key': settings.azure_speech_key}
            if hasattr(settings, 'azure_speech_region') and settings.azure_speech_region:
                config_dict['azure']['region'] = settings.azure_speech_region
        
        if hasattr(settings, 'google_application_credentials') and settings.google_application_credentials:
            config_dict['google'] = {'credentials_path': settings.google_application_credentials}
        
        if hasattr(settings, 'soniox_api_key') and settings.soniox_api_key:
            config_dict['soniox'] = {'api_key': settings.soniox_api_key}
        
        # TTS Providers  
        if hasattr(settings, 'elevenlabs_api_key') and settings.elevenlabs_api_key:
            if 'elevenlabs' not in config_dict:
                config_dict['elevenlabs'] = {}
            config_dict['elevenlabs']['api_key'] = settings.elevenlabs_api_key
        
        # Set preferences based on environment settings
        config_dict['preferences'] = {
            'optimize_for': getattr(settings, 'debabelizer_optimize_for', 'balanced')
        }
        
        return DebabelizerConfig(config_dict)
    
    async def initialize_processors(self):
        """Initialize STT and TTS processors"""
        try:
            print(f"Starting initialization with STT provider: {settings.debabelizer_stt_provider}, TTS provider: {settings.debabelizer_tts_provider}")
            print(f"Available API keys: Deepgram={bool(settings.deepgram_api_key)}, ElevenLabs={bool(settings.elevenlabs_api_key)}, OpenAI={bool(settings.openai_api_key)}")
            
            # Create STT processor
            if settings.debabelizer_stt_provider and self._has_stt_credentials():
                self.stt_processor = VoiceProcessor(
                    stt_provider=settings.debabelizer_stt_provider,
                    config=self._config
                )
                print(f"STT processor created with {settings.debabelizer_stt_provider}")
            else:
                print(f"STT provider {settings.debabelizer_stt_provider} not configured or missing API key")
            
            # Create TTS processor
            if settings.debabelizer_tts_provider and self._has_tts_credentials():
                self.tts_processor = VoiceProcessor(
                    tts_provider=settings.debabelizer_tts_provider,
                    config=self._config
                )
                print(f"TTS processor created with {settings.debabelizer_tts_provider}")
            else:
                print(f"TTS provider {settings.debabelizer_tts_provider} not configured or missing API key")
            
            print(f"Initialization complete. STT: {bool(self.stt_processor)}, TTS: {bool(self.tts_processor)}")
        except Exception as e:
            print(f"Error initializing processors: {e}")
            traceback.print_exc()
    
    def _has_stt_credentials(self):
        """Check if STT provider has required credentials"""
        provider = settings.debabelizer_stt_provider
        return (
            (provider == 'deepgram' and settings.deepgram_api_key) or
            (provider == 'openai' and settings.openai_api_key) or
            (provider == 'azure' and settings.azure_speech_key) or
            (provider == 'soniox' and settings.soniox_api_key) or
            (provider == 'whisper') or  # Whisper doesn't need API key
            (provider == 'google' and settings.google_application_credentials)
        )
    
    def _has_tts_credentials(self):
        """Check if TTS provider has required credentials"""
        provider = settings.debabelizer_tts_provider
        return (
            (provider == 'elevenlabs' and settings.elevenlabs_api_key) or
            (provider == 'openai' and settings.openai_api_key) or
            (provider == 'azure' and settings.azure_speech_key) or
            (provider == 'google' and settings.google_application_credentials)
        )
    
    def get_default_voice(self):
        """Get appropriate default voice based on provider"""
        default_voice = "alloy"  # OpenAI voice
        if settings.debabelizer_tts_provider == "elevenlabs":
            default_voice = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs Rachel voice ID
        elif settings.debabelizer_tts_provider == "azure":
            default_voice = "en-US-JennyNeural"  # Azure voice
        elif settings.debabelizer_tts_provider == "google":
            default_voice = "en-US-Standard-A"  # Google voice
        return default_voice
    
    async def debabelize_text(self, text: str) -> str:
        """
        Process text through debabelizer voice pipeline:
        Text -> TTS -> Audio -> STT -> Corrected Text
        """
        try:
            if not self.tts_processor or not self.stt_processor:
                return text
            
            # Convert text to speech
            tts_result = await self.tts_processor.synthesize(text=text)
            
            # Convert audio back to text
            stt_result = await self.stt_processor.transcribe_audio(
                audio_data=tts_result.audio_data,
                audio_format=settings.elevenlabs_output_format.split('_')[0]
            )
            
            return stt_result.text
            
        except Exception as e:
            traceback.print_exc()
            print(f"Debabelizer error: {e}")
            return text

# Global voice service instance
voice_service = VoiceService()