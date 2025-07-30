import { useState, useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import MessageInput, { MessageInputHandle } from './MessageInput';
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
  const messageInputRef = useRef<MessageInputHandle>(null);
  const keepAliveIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Focus input when loading completes and mic is active
    if (!isLoading && isRecording) {
      messageInputRef.current?.focus();
    }
  }, [isLoading, isRecording]);

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
      // Start recording using Thanotopolis-style PCM streaming
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            channelCount: 1,
            sampleRate: 16000,       // Match backend sample rate
            echoCancellation: true,  // Keep for clean audio
            noiseSuppression: false, // Disable to preserve speech nuances
            autoGainControl: false,  // Disable to maintain consistent levels
            // Advanced constraints for optimal speech recognition
            advanced: [
              { echoCancellation: { exact: true } },
              { noiseSuppression: { exact: false } },
              { autoGainControl: { exact: false } }
            ]
          }
        });
        
        console.log('Got media stream:', stream);
        const audioTrack = stream.getAudioTracks()[0];
        console.log('Audio track settings:', audioTrack.getSettings());

        // Connect to WebSocket for streaming STT
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
        let ws = new WebSocket(`${wsUrl}/ws/stt`);
        wsRef.current = ws;

        // Set up Web Audio API for PCM processing
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        
        // Create a new MediaStream with the same tracks to ensure compatibility
        const newStream = new MediaStream([audioTrack]);
        
        // Create audio nodes
        const source = audioContext.createMediaStreamSource(newStream);
        // Use smaller buffer size for lower latency
        const processor = audioContext.createScriptProcessor(256, 1, 1);  // Even smaller for faster response

        let isFirstAudioFrame = true;
        let recentAudioFramesWithActivity = 0;
        const RECENT_AUDIO_THRESHOLD = 2; // Reduced threshold for faster processing

        // Calculate resampling ratio
        const sourceSampleRate = audioContext.sampleRate;
        const targetSampleRate = 16000;
        const resampleRatio = targetSampleRate / sourceSampleRate;
        
        processor.onaudioprocess = (event) => {
          // If WebSocket is closed, try to reconnect when we have audio input
          if (ws.readyState !== WebSocket.OPEN) {
            console.log('WebSocket is closed, attempting to reconnect...');
            const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
            const newWs = new WebSocket(`${wsUrl}/ws/stt`);
            wsRef.current = newWs;
            
            // Copy the same event handlers to the new WebSocket
            newWs.onopen = ws.onopen;
            newWs.onmessage = ws.onmessage;
            newWs.onerror = ws.onerror;
            newWs.onclose = ws.onclose;
            
            // Update the ws reference for this processor
            ws = newWs;
            (ws as any).audioContext = audioContext;
            (ws as any).processor = processor;
            (ws as any).source = source;
            (ws as any).stream = newStream;
            (ws as any).originalStream = stream;
            
            // Don't process audio until the new connection is established
            return;
          }

          const inputData = event.inputBuffer.getChannelData(0);
          
          // Check if there's actual audio with improved sensitivity
          let hasAudio = false;
          let maxAmplitude = 0;
          let avgAmplitude = 0;
          let nonZeroSamples = 0;
          
          for (let i = 0; i < inputData.length; i++) {
            const amplitude = Math.abs(inputData[i]);
            maxAmplitude = Math.max(maxAmplitude, amplitude);
            avgAmplitude += amplitude;
            if (amplitude > 0.001) { // More sensitive threshold
              nonZeroSamples++;
            }
            if (amplitude > 0.003) { // Lower threshold for detection
              hasAudio = true;
            }
          }
          
          avgAmplitude /= inputData.length;
          
          // Enhanced detection: also consider if we have enough non-zero samples
          if (!hasAudio && nonZeroSamples > inputData.length * 0.1) {
            hasAudio = avgAmplitude > 0.0015; // Backup detection for quiet speech
          }
          
          // Update recent activity tracker
          if (hasAudio) {
            recentAudioFramesWithActivity = RECENT_AUDIO_THRESHOLD;
          } else {
            recentAudioFramesWithActivity = Math.max(0, recentAudioFramesWithActivity - 1);
          }
          
          // Process if we have audio or recent audio activity
          if (!hasAudio && recentAudioFramesWithActivity === 0 && !isFirstAudioFrame) {
            return; // Skip silence frames after initial frame
          }
          
          // Resample to 16kHz if needed
          let resampledData;
          if (sourceSampleRate !== targetSampleRate) {
            const targetLength = Math.floor(inputData.length * resampleRatio);
            resampledData = new Float32Array(targetLength);
            
            // Simple linear interpolation resampling
            for (let i = 0; i < targetLength; i++) {
              const srcIndex = i / resampleRatio;
              const srcIndexFloor = Math.floor(srcIndex);
              const srcIndexCeil = Math.ceil(srcIndex);
              
              if (srcIndexCeil >= inputData.length) {
                resampledData[i] = inputData[inputData.length - 1];
              } else {
                const fraction = srcIndex - srcIndexFloor;
                resampledData[i] = inputData[srcIndexFloor] * (1 - fraction) + inputData[srcIndexCeil] * fraction;
              }
            }
          } else {
            resampledData = inputData;
          }
          
          // Convert Float32 to Int16 PCM with optimized processing
          const pcmData = new Int16Array(resampledData.length);
          
          // Apply dynamic gain based on audio level
          const gain = maxAmplitude < 0.1 ? 2.0 : (maxAmplitude < 0.3 ? 1.5 : 1.2);
          
          for (let i = 0; i < resampledData.length; i++) {
            // Apply dynamic gain for better recognition
            const boostedSample = resampledData[i] * gain;
            const clampedSample = Math.max(-1, Math.min(1, boostedSample));
            // Convert to 16-bit signed integer
            pcmData[i] = clampedSample < 0 ? clampedSample * 0x8000 : clampedSample * 0x7FFF;
          }

          // Debug audio levels when we have significant audio
          // Commented out to reduce console spam
          // if (hasAudio) {
          //   const maxAmplitude = Math.max(...Array.from(pcmData).map(Math.abs));
          //   console.log(`Sending audio - amplitude: ${maxAmplitude}, frames with activity: ${recentAudioFramesWithActivity}`);
          // }
          
          // Send PCM data to backend
          ws.send(pcmData.buffer);
          isFirstAudioFrame = false;
        };

        source.connect(processor);
        processor.connect(audioContext.destination);

        // Store references for cleanup
        (ws as any).audioContext = audioContext;
        (ws as any).processor = processor;
        (ws as any).source = source;
        (ws as any).stream = newStream;
        (ws as any).originalStream = stream;

        ws.onopen = () => {
          console.log('WebSocket connected for STT - PCM streaming mode');
          setIsRecording(true);
          
          // Focus the message input when recording starts (if not loading)
          if (!isLoading) {
            messageInputRef.current?.focus();
          }
          
          // Set up keepalive ping every 30 seconds to prevent timeout
          keepAliveIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              // Send empty buffer as keepalive
              ws.send(new ArrayBuffer(0));
            }
          }, 30000);
        };

        ws.onmessage = (event) => {
          console.log('Raw WebSocket message received:', event.data, 'isLoading:', isLoading);
          const data = JSON.parse(event.data);
          console.log('Parsed WebSocket data:', data);
          if (data.error) {
            console.error('STT error:', data.error);
          } else if (data.text) {
            console.log(`STT result: "${data.text}" (final: ${data.is_final}), isLoading: ${isLoading}`);
            if (data.is_final) {
              // Accumulate transcribed text in the message input instead of auto-sending
              messageInputRef.current?.appendValue(data.text);
              
              // Continue recording for next utterance
              console.log('Continuing to record for next utterance...');
              
              // Always focus input after transcription, regardless of loading state
              messageInputRef.current?.focus();
            }
            // For interim results, we could show them in the UI but not send as messages
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
        };

      } catch (error) {
        console.error('Error starting recording:', error);
        alert('Unable to access microphone. Please check permissions.');
      }
    } else {
      // Stop recording - cleanup Web Audio API components
      if (wsRef.current) {
        const ws = wsRef.current as any;
        
        // Clear keepalive interval
        if (keepAliveIntervalRef.current) {
          clearInterval(keepAliveIntervalRef.current);
          keepAliveIntervalRef.current = null;
        }
        
        // Clean up Web Audio API components
        if (ws.processor) {
          ws.processor.disconnect();
        }
        if (ws.source) {
          ws.source.disconnect();
        }
        if (ws.audioContext && ws.audioContext.state !== 'closed') {
          ws.audioContext.close();
        }
        if (ws.stream) {
          ws.stream.getTracks().forEach((track: MediaStreamTrack) => track.stop());
        }
        if (ws.originalStream) {
          ws.originalStream.getTracks().forEach((track: MediaStreamTrack) => track.stop());
        }
        
        // Close WebSocket
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
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
        <MessageInput ref={messageInputRef} onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}