# Audio buffering configuration for fake streaming approach - balanced latency vs reliability
AUDIO_BUFFER_CONFIG = {
    "min_buffer_size": 12000,      # ~0.75 second at 16kHz PCM - balanced for reliability
    "max_buffer_size": 28000,      # ~1.75 seconds at 16kHz PCM - moderate reduction
    "silence_timeout": 0.4,        # 400ms timeout for processing buffer - moderate improvement
    "sample_rate": 16000,          # PCM sample rate from frontend
    "channels": 1                  # Mono audio
}

class AudioBufferManager:
    def __init__(self):
        self.buffering_sessions = {}
    
    def create_session(self, session_id: str):
        """Create a new audio buffering session"""
        self.buffering_sessions[session_id] = {
            "audio_buffer": bytearray(),
            "last_audio_time": None,
            "last_process_time": None
        }
    
    def add_audio_data(self, session_id: str, data: bytes, current_time: float):
        """Add audio data to session buffer"""
        if session_id not in self.buffering_sessions:
            return False
        
        session = self.buffering_sessions[session_id]
        session["audio_buffer"].extend(data)
        session["last_audio_time"] = current_time
        return True
    
    def should_process_buffer(self, session_id: str, current_time: float) -> bool:
        """Determine if buffer should be processed based on size and timing"""
        if session_id not in self.buffering_sessions:
            return False
        
        session = self.buffering_sessions[session_id]
        buffer_size = len(session["audio_buffer"])
        
        time_since_last_process = (
            current_time - session["last_process_time"] 
            if session["last_process_time"] else float('inf')
        )
        
        # Process with balanced approach for reliability and latency
        should_process = (
            buffer_size >= AUDIO_BUFFER_CONFIG["max_buffer_size"] or  # Prevent memory overflow
            (buffer_size >= AUDIO_BUFFER_CONFIG["min_buffer_size"] and 
             time_since_last_process >= AUDIO_BUFFER_CONFIG["silence_timeout"])  # Use configured timeout
        )
        
        return should_process and buffer_size > 0
    
    def extract_buffer(self, session_id: str, current_time: float) -> bytes:
        """Extract buffered audio and reset buffer"""
        if session_id not in self.buffering_sessions:
            return b''
        
        session = self.buffering_sessions[session_id]
        buffered_audio = bytes(session["audio_buffer"])
        
        # Clear the buffer and update process time
        session["audio_buffer"] = bytearray()
        session["last_process_time"] = current_time
        
        return buffered_audio
    
    def get_final_buffer(self, session_id: str) -> bytes:
        """Get any remaining audio in buffer for final processing"""
        if session_id not in self.buffering_sessions:
            return b''
        
        session = self.buffering_sessions[session_id]
        return bytes(session["audio_buffer"])
    
    def cleanup_session(self, session_id: str):
        """Clean up buffering session"""
        if session_id in self.buffering_sessions:
            del self.buffering_sessions[session_id]
    
    def get_session_count(self) -> int:
        """Get number of active buffering sessions"""
        return len(self.buffering_sessions)

# Global audio buffer manager
audio_buffer_manager = AudioBufferManager()