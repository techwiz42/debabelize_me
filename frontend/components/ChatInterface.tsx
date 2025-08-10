import { useState, useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import MessageInput, { MessageInputHandle } from './MessageInput';
import { apiService } from '../services/api';
import { useAuth } from './AuthProvider';
import { useRouter } from 'next/navigation';

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
  console.log('🔥 CHATINTERFACE LOADED - NEW VERSION WITH FIXES 🔥', new Date().toISOString());
  
  const { user, logout } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaybackEnabled, setIsPlaybackEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [wasRecordingBeforeReply, setWasRecordingBeforeReply] = useState(false);
  const wasRecordingBeforeReplyRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const messageInputRef = useRef<MessageInputHandle>(null);
  const keepAliveIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const isWebSocketReady = useRef<boolean>(false);
  const reconnectAttempts = useRef<number>(0);
  const maxReconnectAttempts = 3;
  const currentUtteranceRef = useRef<string>('');
  const utteranceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const userStoppedRecording = useRef<boolean>(false);
  const isRecordingRef = useRef<boolean>(false);
  const isSendingMessage = useRef<boolean>(false);

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

  // Pre-establish WebSocket connection and AudioContext for faster first utterance
  useEffect(() => {
    const preEstablishConnection = async () => {
      // Pre-create AudioContext (must be done after user interaction)
      if (!audioContextRef.current) {
        try {
          audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
          // Suspend immediately - will resume when recording starts
          if (audioContextRef.current.state === 'running') {
            await audioContextRef.current.suspend();
          }
        } catch (error) {
          console.warn('Could not pre-create AudioContext:', error);
        }
      }
    };

    // Pre-establish connection after a short delay to avoid immediate startup overhead
    const timer = setTimeout(preEstablishConnection, 1000);
    return () => {
      clearTimeout(timer);
      
      // Clean up on component unmount
      if (wsRef.current) {
        console.log('Component unmounting - cleaning up WebSocket');
        try {
          if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
            wsRef.current.close();
          }
        } catch (error) {
          console.warn('Error closing WebSocket on unmount:', error);
        }
      }
      
      // Clean up audio context
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        try {
          audioContextRef.current.close();
        } catch (error) {
          console.warn('Error closing AudioContext on unmount:', error);
        }
      }
      
      // Clear any pending timeouts
      if (keepAliveIntervalRef.current) {
        clearInterval(keepAliveIntervalRef.current);
      }
      if (utteranceTimeoutRef.current) {
        clearTimeout(utteranceTimeoutRef.current);
      }
    };
  }, []);

  const handleSendMessage = async (content: string) => {
    // Set flag to indicate we're sending a message
    isSendingMessage.current = true;
    
    // First, finalize any pending utterance before creating the message
    if (currentUtteranceRef.current.trim()) {
      console.log('Finalizing pending utterance before send:', currentUtteranceRef.current);
      // Clear the timeout since we're finalizing now
      if (utteranceTimeoutRef.current) {
        clearTimeout(utteranceTimeoutRef.current);
        utteranceTimeoutRef.current = null;
      }
      // Append the pending utterance to the message
      messageInputRef.current?.appendValue(currentUtteranceRef.current.trim());
      currentUtteranceRef.current = '';
      // Wait a tiny bit for the state to update
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };
    
    // Remember if we were recording before sending message
    const wasRecording = isRecordingRef.current || isRecording;
    console.log('Recording state check:', { isRecording, isRecordingRef: isRecordingRef.current, wasRecording });
    setWasRecordingBeforeReply(wasRecording);
    wasRecordingBeforeReplyRef.current = wasRecording;
    
    // Stop recording when sending message
    if (wasRecording) {
      console.log('Stopping recording on message send');
      toggleRecording(true); // true = programmatic stop
      // toggleRecording will handle finalizing any pending utterance
    }
    
    // Clear interim text to prevent carry-over
    messageInputRef.current?.clearInterimText();
    
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
      
      // Function to restart recording if it was active before
      const restartRecordingIfNeeded = async () => {
        const shouldRestart = wasRecordingBeforeReplyRef.current || wasRecordingBeforeReply;
        console.log('restartRecordingIfNeeded called:', {
          shouldRestart,
          wasRecordingBeforeReply,
          wasRecordingBeforeReplyRef: wasRecordingBeforeReplyRef.current,
          isRecording,
          isRecordingRef: isRecordingRef.current,
          userStoppedRecording: userStoppedRecording.current
        });
        
        if (shouldRestart) {
          console.log('Recording should restart - clearing flags and calling toggleRecording');
          // Clear all flags that might prevent restart
          userStoppedRecording.current = false;
          setWasRecordingBeforeReply(false);
          wasRecordingBeforeReplyRef.current = false;
          
          // Always force start, regardless of current state
          await toggleRecording(false, true); // false = not programmatic stop, true = force start
          messageInputRef.current?.focus();
        }
      };
      
      // Play audio if playback is enabled
      if (isPlaybackEnabled) {
        try {
          const audioBlob = await apiService.textToSpeech(response.response, undefined, response.response_language || selectedLanguage);
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          audio.play();
          
          // Clean up URL after audio finishes and restart recording
          audio.addEventListener('ended', () => {
            URL.revokeObjectURL(audioUrl);
            console.log('TTS audio playback ended');
            // Restart recording after TTS playback completes
            restartRecordingIfNeeded();
          });
        } catch (error) {
          console.error('Error playing audio:', error);
          // If TTS fails, still restart recording
          setTimeout(restartRecordingIfNeeded, 500);
        }
      } else {
        // If TTS is disabled, restart recording immediately after message display
        setTimeout(restartRecordingIfNeeded, 500);
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
      
      // Restart recording even after error
      if (wasRecordingBeforeReplyRef.current || wasRecordingBeforeReply) {
        setTimeout(async () => {
          console.log('Restarting recording after error');
          userStoppedRecording.current = false;
          setWasRecordingBeforeReply(false);
          wasRecordingBeforeReplyRef.current = false;
          await toggleRecording(false, true);
          messageInputRef.current?.focus();
        }, 500);
      }
    } finally {
      setIsLoading(false);
      // Always focus input after loading completes
      messageInputRef.current?.focus();
      // Clear sending flag
      isSendingMessage.current = false;
    }
  };

  const toggleRecording = async (programmaticStop = false, forceStart = false) => {
    console.log('toggleRecording called:', {
      isRecording,
      isRecordingRef: isRecordingRef.current,
      programmaticStop,
      forceStart,
      userStoppedRecording: userStoppedRecording.current
    });
    
    if (!isRecording || forceStart) {
      // Clear the user stopped flag when starting recording
      userStoppedRecording.current = false;
      // Reset reconnection attempts for fresh start
      reconnectAttempts.current = 0;
      
      // Clean up any existing WebSocket connection before starting new one
      if (wsRef.current) {
        console.log('Cleaning up existing WebSocket before starting new recording');
        try {
          if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
            wsRef.current.close();
          }
        } catch (error) {
          console.warn('Error closing existing WebSocket:', error);
        }
        wsRef.current = null;
      }
      
      // Set recording state immediately
      setIsRecording(true);
      isRecordingRef.current = true;
      console.log('Recording state set to true');
      
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
        // Get session token from cookies for authentication
        console.log('All cookies:', document.cookie);
        const sessionToken = document.cookie
          .split('; ')
          .find(row => row.startsWith('session_token='))
          ?.split('=')[1];
        console.log('Extracted session token:', sessionToken ? sessionToken.substring(0, 10) + '...' : 'null');
        const wsUrlWithAuth = sessionToken 
          ? `${wsUrl}/ws/stt?session_token=${sessionToken}`
          : `${wsUrl}/ws/stt`;
        console.log('WebSocket URL:', wsUrlWithAuth);
        let ws = new WebSocket(wsUrlWithAuth);
        wsRef.current = ws;

        // Use pre-created AudioContext or create new one for PCM processing
        let audioContext = audioContextRef.current;
        if (!audioContext || audioContext.state === 'closed') {
          audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          audioContextRef.current = audioContext;
        }
        
        // Resume if suspended
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
        }
        
        // Create a new MediaStream with the same tracks to ensure compatibility
        const newStream = new MediaStream([audioTrack]);
        
        // Create audio nodes
        const source = audioContext.createMediaStreamSource(newStream);
        // Use smallest buffer size for lowest latency
        const processor = audioContext.createScriptProcessor(256, 1, 1);  // 256 samples = ~16ms at 16kHz

        let isFirstAudioFrame = true;
        let recentAudioFramesWithActivity = 0;
        const RECENT_AUDIO_THRESHOLD = 2; // Reduced threshold for faster processing
        let isWebSocketReady = false; // Track when WebSocket is ready
        
        // Audio buffer to store chunks while WebSocket is connecting
        const audioBuffer: ArrayBuffer[] = [];
        const MAX_BUFFER_SIZE = 20; // Store up to 20 chunks (about 320ms at 16ms per chunk)

        // Calculate resampling ratio
        const sourceSampleRate = audioContext.sampleRate;
        const targetSampleRate = 16000;
        const resampleRatio = targetSampleRate / sourceSampleRate;
        
        processor.onaudioprocess = (event) => {
          // Stop processing if user has explicitly stopped recording
          if (userStoppedRecording.current) {
            return;
          }
          
          // Process audio even if WebSocket is not ready - we'll buffer it
          
          // If WebSocket is not open, check if it's still connecting
          if (ws.readyState !== WebSocket.OPEN) {
            // If it's still connecting, wait - don't treat as closed
            if (ws.readyState === WebSocket.CONNECTING) {
              return;
            }
            
            // Only attempt reconnect if actually closed
            if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
              if (reconnectAttempts.current < maxReconnectAttempts) {
                console.log(`WebSocket is closed, attempting to reconnect... (${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);
                reconnectAttempts.current++;
                
                const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
                // Get session token from cookies for authentication (reconnection)
                console.log('Reconnection - All cookies:', document.cookie);
                const sessionToken = document.cookie
                  .split('; ')
                  .find(row => row.startsWith('session_token='))
                  ?.split('=')[1];
                console.log('Reconnection - Extracted session token:', sessionToken ? sessionToken.substring(0, 10) + '...' : 'null');
                const wsUrlWithAuth = sessionToken 
                  ? `${wsUrl}/ws/stt?session_token=${sessionToken}`
                  : `${wsUrl}/ws/stt`;
                console.log('Reconnection - WebSocket URL:', wsUrlWithAuth);
                const newWs = new WebSocket(wsUrlWithAuth);
                wsRef.current = newWs;
                
                // Copy the same event handlers to the new WebSocket
                const originalOnOpen = ws.onopen;
                newWs.onopen = (event) => {
                  console.log('Reconnected WebSocket opened');
                  isWebSocketReady = true; // Set ready flag for reconnected WebSocket
                  if (originalOnOpen) {
                    originalOnOpen.call(newWs, event);
                  }
                };
                newWs.onmessage = ws.onmessage;
                newWs.onerror = ws.onerror;
                newWs.onclose = ws.onclose;
                
                // Update the ws reference for this processor
                ws = newWs;
                isWebSocketReady = false; // Reset ready flag for new connection
                (ws as any).audioContext = audioContext;
                (ws as any).processor = processor;
                (ws as any).source = source;
                (ws as any).stream = newStream;
                (ws as any).originalStream = stream;
              } else {
                console.warn('Max WebSocket reconnection attempts reached, stopping recording');
                // Stop recording when max attempts reached only if currently recording
                if (isRecording && !userStoppedRecording.current) {
                  userStoppedRecording.current = true;
                  setIsRecording(false);
                  isRecordingRef.current = false;
                }
                return;
              }
            }
            
            // Don't process audio until the connection is established
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
          
          // If WebSocket is not ready, buffer the audio
          if (!isWebSocketReady) {
            if (audioBuffer.length < MAX_BUFFER_SIZE) {
              audioBuffer.push(pcmData.buffer.slice(0)); // Clone the buffer
            }
            isFirstAudioFrame = false;
            return;
          }
          
          // Send any buffered audio first (only once when WebSocket becomes ready)
          if (audioBuffer.length > 0) {
            console.log(`Sending ${audioBuffer.length} buffered audio chunks`);
            for (const bufferedChunk of audioBuffer) {
              if (ws.readyState === WebSocket.OPEN) {
                ws.send(bufferedChunk);
              }
            }
            audioBuffer.length = 0; // Clear the buffer
          }
          
          // Send current PCM data to backend
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(pcmData.buffer);
          }
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
          isWebSocketReady = true; // Mark WebSocket as ready
          // Recording state already set at the beginning of toggleRecording
          reconnectAttempts.current = 0; // Reset reconnection counter on successful connection
          
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
            console.log(`STT result: "${data.text}" (final: ${data.is_final}, word: ${data.is_word}), isLoading: ${isLoading}`);
            
            if (data.is_final && data.is_word) {
              // Handle word-level final results from Soniox
              // Build up the complete utterance from individual words
              currentUtteranceRef.current += (currentUtteranceRef.current ? ' ' : '') + data.text;
              
              // Show the current utterance being built as interim text
              console.log('Building utterance, showing interim:', currentUtteranceRef.current);
              messageInputRef.current?.showInterimText(currentUtteranceRef.current);
              
              // Clear any existing timeout
              if (utteranceTimeoutRef.current) {
                clearTimeout(utteranceTimeoutRef.current);
              }
              
              // Set timeout to finalize utterance after pause (1 second of no new words)
              utteranceTimeoutRef.current = setTimeout(() => {
                if (currentUtteranceRef.current.trim()) {
                  console.log('Finalizing complete utterance:', currentUtteranceRef.current);
                  messageInputRef.current?.appendValue(currentUtteranceRef.current.trim());
                  messageInputRef.current?.clearInterimText();
                  currentUtteranceRef.current = '';
                  // Always focus input after transcription
                  messageInputRef.current?.focus();
                }
              }, 500); // Shorter timeout for faster finalization of single phrases
              
            } else if (data.is_final && !data.is_word) {
              // Handle complete utterance final results (for providers that send complete phrases)
              console.log('Complete utterance received, calling appendValue with:', data.text);
              messageInputRef.current?.appendValue(data.text);
              messageInputRef.current?.clearInterimText();
              
              // Clear word-level utterance building
              currentUtteranceRef.current = '';
              if (utteranceTimeoutRef.current) {
                clearTimeout(utteranceTimeoutRef.current);
                utteranceTimeoutRef.current = null;
              }
              
              // Always focus input after transcription
              messageInputRef.current?.focus();
              
            } else {
              // For interim results, show in real-time preview
              if (data.text.trim()) {
                console.log('Calling showInterimText with:', data.text);
                messageInputRef.current?.showInterimText(data.text);
              }
            }
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          
          // Clear utterance timeout when connection closes
          if (utteranceTimeoutRef.current) {
            clearTimeout(utteranceTimeoutRef.current);
            utteranceTimeoutRef.current = null;
          }
          
          // Finalize any pending utterance
          if (currentUtteranceRef.current.trim()) {
            console.log('Connection closed, finalizing pending utterance:', currentUtteranceRef.current);
            messageInputRef.current?.appendValue(currentUtteranceRef.current.trim());
            messageInputRef.current?.clearInterimText();
            currentUtteranceRef.current = '';
          }
        };

      } catch (error) {
        console.error('Error starting recording:', error);
        alert('Unable to access microphone. Please check permissions.');
      }
    } else {
      // Stop recording - set flag to prevent WebSocket onopen from overriding
      console.log(programmaticStop ? 'Programmatically stopping recording' : 'User clicked to stop recording');
      console.trace('Recording stop call stack');
      userStoppedRecording.current = !programmaticStop;
      // Always set state first to ensure UI updates
      setIsRecording(false);
      isRecordingRef.current = false;
      
      // Clear keepalive interval
      if (keepAliveIntervalRef.current) {
        clearInterval(keepAliveIntervalRef.current);
        keepAliveIntervalRef.current = null;
      }
      
      // Clear any pending utterance timeout
      if (utteranceTimeoutRef.current) {
        clearTimeout(utteranceTimeoutRef.current);
        utteranceTimeoutRef.current = null;
      }
      
      // Finalize any pending utterance when stopping recording
      if (currentUtteranceRef.current.trim()) {
        console.log('Recording stopped, finalizing pending utterance:', currentUtteranceRef.current);
        messageInputRef.current?.appendValue(currentUtteranceRef.current.trim());
        messageInputRef.current?.clearInterimText();
        currentUtteranceRef.current = '';
      }
      
      // Cleanup Web Audio API components and WebSocket
      if (wsRef.current) {
        const ws = wsRef.current as any;
        
        // Clean up Web Audio API components
        try {
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
        } catch (error) {
          console.warn('Error during audio cleanup:', error);
        }
        
        // Close WebSocket
        try {
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close();
          }
        } catch (error) {
          console.warn('Error closing WebSocket:', error);
        }
        
        // Clear WebSocket reference
        wsRef.current = null;
      }
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

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/auth');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="header-title">
          <h1>Debabelize</h1>
        </div>
        <div className="header-controls">
          <div className="left-controls">
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
                type="button"
                className={`audio-control-btn ${isRecording ? 'recording' : ''}`}
                onClick={() => toggleRecording(false, false)}
                title={isRecording ? 'Stop Recording' : 'Start Recording'}
              >
                {isRecording ? '🛑' : '🎤'}
              </button>
              <button
                type="button"
                className={`audio-control-btn ${isPlaybackEnabled ? 'enabled' : 'disabled'}`}
                onClick={togglePlayback}
                title={isPlaybackEnabled ? 'Disable Audio Output' : 'Enable Audio Output'}
              >
                {isPlaybackEnabled ? '🔊' : '🔇'}
              </button>
              <button
                type="button"
                className="audio-control-btn new-chat-btn"
                onClick={clearConversation}
                title="Start New Conversation"
              >
                🆕
              </button>
            </div>
          </div>
          <div className="user-section">
            <span className="welcome-text">Welcome, {user?.email}</span>
            <button
              className="logout-btn"
              onClick={handleLogout}
              title="Logout"
            >
              Logout
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
        <MessageInput ref={messageInputRef} onSendMessage={handleSendMessage} disabled={false} />
      </div>
    </div>
  );
}