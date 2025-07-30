from typing import Dict, List, Optional
import uuid
from datetime import datetime, timedelta

class SessionService:
    def __init__(self):
        self.session_conversations: Dict[str, Dict[str, any]] = {}
        self.session_timeout_hours = 24
        self.cleanup_interval_hours = 1
        self.last_cleanup = datetime.now()
    
    def cleanup_old_sessions(self):
        """Remove sessions that haven't been accessed in SESSION_TIMEOUT_HOURS."""
        current_time = datetime.now()
        
        # Only run cleanup if enough time has passed
        if current_time - self.last_cleanup < timedelta(hours=self.cleanup_interval_hours):
            return
        
        self.last_cleanup = current_time
        timeout_threshold = current_time - timedelta(hours=self.session_timeout_hours)
        
        sessions_to_remove = []
        for session_id, session_data in self.session_conversations.items():
            if session_data.get('last_accessed', current_time) < timeout_threshold:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.session_conversations[session_id]
        
        if sessions_to_remove:
            print(f"Cleaned up {len(sessions_to_remove)} old sessions")
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get existing session or create a new one."""
        self.cleanup_old_sessions()
        
        if not session_id or session_id not in self.session_conversations:
            session_id = str(uuid.uuid4())
            self.session_conversations[session_id] = {
                'conversation_history': [],
                'created_at': datetime.now(),
                'last_accessed': datetime.now()
            }
            print(f"Created new session: {session_id}")
        else:
            # Update last accessed time
            self.session_conversations[session_id]['last_accessed'] = datetime.now()
        
        return session_id
    
    def get_session_conversation_history(self, session_id: str) -> List[dict]:
        """Get conversation history for a specific session."""
        if session_id in self.session_conversations:
            return self.session_conversations[session_id]['conversation_history']
        return []
    
    def clear_session_conversation(self, session_id: Optional[str] = None):
        """Clear conversation history for a specific session or all sessions."""
        if session_id:
            # Clear specific session
            if session_id in self.session_conversations:
                self.session_conversations[session_id]['conversation_history'] = []
                return {"message": f"Conversation history cleared for session {session_id}"}
            else:
                return {"message": "Session not found"}
        else:
            # Clear all sessions (backward compatibility)
            self.session_conversations.clear()
            return {"message": "All conversation histories cleared"}

# Global session service instance
session_service = SessionService()