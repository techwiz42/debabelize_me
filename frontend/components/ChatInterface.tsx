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

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaybackEnabled, setIsPlaybackEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
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
      const response = await apiService.sendMessage(content);
      
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
          const audioBlob = await apiService.textToSpeech(response.response);
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

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="header-title">
          <h1>Debabelize</h1>
        </div>
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
        </div>
      </div>

      <div className="messages-container">
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}