import { useState, useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import MessageInput from './MessageInput';
import { apiService } from '../services/api';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

const SUPPORTED_LANGUAGES = [
  { code: 'auto', name: 'Auto-detect' },
  { code: 'af', name: 'Afrikaans' },
  { code: 'sq', name: 'Albanian' },
  { code: 'ar', name: 'Arabic' },
  { code: 'az', name: 'Azerbaijani' },
  { code: 'eu', name: 'Basque' },
  { code: 'be', name: 'Belarusian' },
  { code: 'bn', name: 'Bengali' },
  { code: 'bs', name: 'Bosnian' },
  { code: 'bg', name: 'Bulgarian' },
  { code: 'ca', name: 'Catalan' },
  { code: 'zh', name: 'Chinese' },
  { code: 'hr', name: 'Croatian' },
  { code: 'cs', name: 'Czech' },
  { code: 'da', name: 'Danish' },
  { code: 'nl', name: 'Dutch' },
  { code: 'en', name: 'English' },
  { code: 'et', name: 'Estonian' },
  { code: 'fi', name: 'Finnish' },
  { code: 'fr', name: 'French' },
  { code: 'gl', name: 'Galician' },
  { code: 'de', name: 'German' },
  { code: 'el', name: 'Greek' },
  { code: 'gu', name: 'Gujarati' },
  { code: 'he', name: 'Hebrew' },
  { code: 'hi', name: 'Hindi' },
  { code: 'hu', name: 'Hungarian' },
  { code: 'id', name: 'Indonesian' },
  { code: 'it', name: 'Italian' },
  { code: 'ja', name: 'Japanese' },
  { code: 'kn', name: 'Kannada' },
  { code: 'kk', name: 'Kazakh' },
  { code: 'ko', name: 'Korean' },
  { code: 'lv', name: 'Latvian' },
  { code: 'lt', name: 'Lithuanian' },
  { code: 'mk', name: 'Macedonian' },
  { code: 'ms', name: 'Malay' },
  { code: 'ml', name: 'Malayalam' },
  { code: 'mr', name: 'Marathi' },
  { code: 'no', name: 'Norwegian' },
  { code: 'fa', name: 'Persian' },
  { code: 'pl', name: 'Polish' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'pa', name: 'Punjabi' },
  { code: 'ro', name: 'Romanian' },
  { code: 'ru', name: 'Russian' },
  { code: 'sr', name: 'Serbian' },
  { code: 'sk', name: 'Slovak' },
  { code: 'sl', name: 'Slovenian' },
  { code: 'es', name: 'Spanish' },
  { code: 'sw', name: 'Swahili' },
  { code: 'sv', name: 'Swedish' },
  { code: 'tl', name: 'Tagalog' },
  { code: 'ta', name: 'Tamil' },
  { code: 'te', name: 'Telugu' },
  { code: 'th', name: 'Thai' },
  { code: 'tr', name: 'Turkish' },
  { code: 'uk', name: 'Ukrainian' },
  { code: 'ur', name: 'Urdu' },
  { code: 'vi', name: 'Vietnamese' },
  { code: 'cy', name: 'Welsh' }
];

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaybackEnabled, setIsPlaybackEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
      const response = await apiService.sendMessage(content, selectedLanguage, sessionId || undefined);
      
      // Store the session ID from the response
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        sender: 'assistant',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Play audio if playback is enabled
      if (isPlaybackEnabled) {
        try {
          const audioBlob = await apiService.textToSpeech(response.response, undefined, response.response_language || selectedLanguage);
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          audio.play();
          
          // Clean up URL after audio finishes
          audio.addEventListener('ended', () => {
            URL.revokeObjectURL(audioUrl);
          });
        } catch (error) {
          console.error('Error playing audio:', error);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        sender: 'assistant',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleRecording = async () => {
    if (!isRecording) {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        // Connect to WebSocket for streaming STT
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
        const ws = new WebSocket(`${wsUrl}/ws/stt`);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('WebSocket connected for STT');
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.error) {
            console.error('STT error:', data.error);
          } else if (data.is_final && data.text) {
            // Send the final transcribed text as a message
            handleSendMessage(data.text);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
            // Send audio data to WebSocket
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(event.data);
            }
          }
        };

        mediaRecorder.start(100); // Send data every 100ms
        setIsRecording(true);
      } catch (error) {
        console.error('Error starting recording:', error);
        alert('Unable to access microphone. Please check permissions.');
      }
    } else {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
      
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      
      setIsRecording(false);
    }
  };

  const togglePlayback = () => {
    setIsPlaybackEnabled(!isPlaybackEnabled);
  };
  
  const clearConversation = async () => {
    if (confirm('Are you sure you want to start a new conversation?')) {
      // Clear messages locally
      setMessages([]);
      
      // Clear server-side conversation if we have a session
      if (sessionId) {
        try {
          await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/clear-conversation`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: sessionId }),
          });
        } catch (error) {
          console.error('Error clearing conversation:', error);
        }
      }
      
      // Reset session ID to start a new session
      setSessionId(null);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="header-title">
          <h1>Debabelize</h1>
        </div>
        <div className="header-controls">
          <select
            className="language-selector"
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            title="Select response language"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
          <div className="audio-controls">
            <button
              className={`audio-control-btn ${isRecording ? 'recording' : ''}`}
              onClick={toggleRecording}
              title={isRecording ? 'Stop Recording' : 'Start Recording'}
            >
              {isRecording ? '🛑' : '🎤'}
            </button>
            <button
              className={`audio-control-btn ${isPlaybackEnabled ? 'enabled' : 'disabled'}`}
              onClick={togglePlayback}
              title={isPlaybackEnabled ? 'Disable Audio Output' : 'Enable Audio Output'}
            >
              {isPlaybackEnabled ? '🔊' : '🔇'}
            </button>
            <button
              className="audio-control-btn new-chat-btn"
              onClick={clearConversation}
              title="Start New Conversation"
            >
              🆕
            </button>
          </div>
        </div>
      </div>

      <div className="messages-container">
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="message-item assistant-message">
            <div className="loading-indicator">
              <div className="loading-circle"></div>
              <span className="loading-text">Babs is thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}