# CLAUDE.md - Project Context for Claude Code

## Claude Configuration
**IMPORTANT**: Always use TodoWrite to track tasks throughout all sessions. This helps maintain context and progress visibility.

## Project Overview
Debabelize Me is a voice-enabled chat application that leverages the **debabelizer module** for all speech-to-text (STT) and text-to-speech (TTS) functionality. The debabelizer module provides a unified, provider-agnostic interface for voice services. The app features a React/Next.js frontend and a FastAPI backend.

**Important**: All STT and TTS functionality is accessed through the debabelizer module - we do not directly integrate with providers like Deepgram or ElevenLabs. See the debabelizer documentation at `~/debabelizer/README.md` for detailed information about the module's capabilities and configuration.

**Current Status**: TTS is fully functional. STT has been implemented using a "fake streaming" approach that is more reliable than true WebSocket streaming:

1. **Phase 1 (2025-07-30a)**: Fixed WebSocket connection errors by resolving parameter conflicts in debabelizer library calls
2. **Phase 2 (2025-07-30b)**: Fixed speech detection by properly configuring audio format handling for WebM/Opus streams from browsers  
3. **Phase 3 (2025-07-30c)**: Implemented "fake streaming" approach using audio buffering and Deepgram's file API instead of true streaming, based on proven Thanotopolis implementation
4. **Phase 4 (2025-07-30d)**: Switched to Thanotopolis-style PCM streaming approach to fix WebM container format issues

   **Root Cause**: WebM chunks from `MediaRecorder.ondataavailable` are incomplete fragments that cannot be processed as valid WebM files by Deepgram's API, causing "corrupt or unsupported data" errors.
   
   **Solution**: Adopted Thanotopolis implementation pattern:
   - **Frontend**: Use Web Audio API (`ScriptProcessorNode`) instead of `MediaRecorder`
   - **Audio Processing**: Convert Float32 → Int16 PCM with 50% signal boost and activity detection
   - **Format**: Send raw PCM data (16kHz, mono) instead of WebM chunks
   - **Backend**: Process PCM data with `audio_format="pcm"` instead of `"webm"`
   
   **Benefits**: Eliminates container format issues, provides better audio quality control, and matches proven working implementation.

5. **Phase 5 (2025-07-30e)**: Fixed WebSocket disconnection after message send

   **Root Cause**: After sending a chat message, the WebSocket connection would close and subsequent speech input would be ignored because the audio processor returned early when detecting a closed WebSocket.
   
   **Solution**: Implemented automatic WebSocket reconnection in audio processor:
   - **Detection**: Audio processor checks WebSocket state before sending data
   - **Reconnection**: When WebSocket is closed but audio input is detected, automatically creates new WebSocket connection
   - **Handler Preservation**: New WebSocket inherits all event handlers from the original connection
   - **Seamless Operation**: Speech transcription continues working after sending messages
   
   **Technical Details**: Changed `const ws` to `let ws` to allow reassignment during reconnection, added reconnection logic in `onaudioprocess` handler.
   
   **Benefits**: Continuous speech transcription functionality regardless of chat message sending, improved user experience with persistent voice input.

6. **Phase 6 (2025-07-30f)**: Optimized latency and improved UX flow

   **Latency Optimizations**:
   - **AudioContext Pre-creation**: Pre-create and suspend AudioContext on component mount to eliminate ~100ms setup delay
   - **Reduced Buffer Sizes**: Optimized backend buffering (0.75s min, 1.75s max, 400ms timeout) for faster transcription
   - **Smaller Frontend Buffers**: Use 256-sample ScriptProcessor buffers (~16ms at 16kHz) for lower latency
   - **Expected Improvements**: ~100-150ms faster first utterance, ~200-400ms faster between utterances
   
   **UX Flow Improvements**:
   - **Auto-restart STT**: Automatically restart speech recording after agent replies complete (tracks `wasRecordingBeforeReply` state)
   - **Smart Focus Management**: Always return focus to MessageInput after agent replies for seamless conversation flow
   - **WebSocket Reconnection Limits**: Prevent browser flooding by limiting reconnection attempts to 3 max, with counter reset on successful connection
   
   **Technical Implementation**:
   - Pre-established AudioContext with suspend/resume pattern
   - State tracking for recording continuity across message sends
   - Limited reconnection attempts with graceful failure handling
   - Consistent input focus management for optimal typing/voice workflow

## Architecture

### Backend (FastAPI)
- **Location**: `/backend/app/main.py`
- **Port**: 8005
- **Key Features**:
  - STT/TTS integration via debabelizer module
  - WebSocket endpoint for streaming STT
  - Chat endpoint with GPT integration
  - Debabelizing pipeline (TTS→STT) for text processing

### Frontend (Next.js)
- **Location**: `/frontend/`
- **Port**: 3005
- **Key Components**:
  - `ChatInterface.tsx` - Main chat UI with voice controls
  - `services/api.ts` - API client for backend communication

## Voice Configuration

### Environment Variables
The app uses provider-agnostic configuration via environment variables:

```bash
# Backend .env
DEEPGRAM_API_KEY=<key>
ELEVENLABS_API_KEY=<key>
DEBABELIZER_STT_PROVIDER=deepgram
DEBABELIZER_TTS_PROVIDER=elevenlabs
DEBABELIZER_OPTIMIZE_FOR=balanced
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128
```

### Providers
- **STT**: Deepgram (configurable via DEBABELIZER_STT_PROVIDER)
- **TTS**: ElevenLabs (configurable via DEBABELIZER_TTS_PROVIDER)

## Key Implementation Details

### Voice Recording
- Mic button in UI starts MediaRecorder
- Audio streams via WebSocket to `/ws/stt` endpoint
- Transcribed text automatically sent as chat message

### Audio Playback
- Speaker button toggles TTS for assistant responses
- Uses `/tts` endpoint to synthesize speech
- Plays audio automatically when enabled

### STT Streaming Technical Details (PCM Streaming Approach)
- **Frontend**: Web Audio API (`ScriptProcessorNode`) processes audio in real-time
- **Audio Processing**: 
  - **Sample Rate**: 16kHz (optimized for speech recognition)
  - **Format**: Int16 PCM with mono channel
  - **Signal Boost**: 50% amplification for better recognition
  - **Activity Detection**: Dynamic thresholds (0.001-0.003) to detect speech
  - **Chunk Size**: 512 samples per audio frame (~32ms at 16kHz)
- **Backend Processing**: 
  - **Fake Streaming**: Uses audio buffering with PCM data instead of WebM containers
  - **Buffer Configuration**: 0.75-1.75 second audio buffers optimized for low latency (Phase 6)
  - **Transcription Method**: Uses Deepgram's file API (`transcribe_chunk`) with raw PCM data
  - **Processing Flow**: PCM Buffer → File API call → Final transcription result
  - **Format**: `audio_format="pcm"`, `sample_rate=16000`, `channels=1`
  - **Timeout**: 400ms processing timeout for responsive transcription
- **Result Flow**: Buffered PCM chunks processed as complete transcriptions, final results sent as chat messages
- **Advantages**: Eliminates WebM container issues, better audio quality control, proven reliability

### Debabelizing
- Text → TTS → Audio → STT pipeline
- Helps identify pronunciation/transcription issues
- Implemented in `debabelize_text()` function

## Development Commands

### Backend
```bash
cd backend
python run.py  # Starts on port 8005
```

### Frontend
```bash
cd frontend
npm run dev    # Starts on port 3005
npm run build  # Production build
```

## Important Notes

1. **CRITICAL: NO LOCALHOST TESTING**: NEVER test localhost endpoints during debugging - servers are not running on localhost during development sessions. Always verify services are running before attempting HTTP requests.
2. **No Localhost Fallbacks**: All URLs must come from environment variables
3. **Provider Agnostic**: Code should not hardcode specific STT/TTS providers
4. **Environment-Based Config**: All provider configuration lives in .env files
5. **WebSocket Streaming**: STT uses WebSocket for real-time transcription
6. **Audio Format**: Browser typically sends webm format for recording

## Common Issues & Solutions

1. **API Key Conflicts**: Ensure environment variables are properly set
2. **WebSocket Connection**: Check NEXT_PUBLIC_WS_URL is correctly configured
3. **Audio Permissions**: Browser requires user permission for microphone access
4. **CORS**: Backend configured to accept requests from frontend domains
5. **STT WebSocket Connection Issues (Phase 1)**: Fixed 2025-07-30a - caused by passing `channels=1` parameter directly to `start_streaming_transcription()` when debabelizer already extracts it from kwargs, causing parameter conflict. Solution: Remove explicit `channels` parameter in `/ws/stt` endpoint.

6. **STT Speech Detection Issues (Phase 2)**: Fixed 2025-07-30b - WebSocket connected successfully but no speech was detected. Root cause analysis revealed:
   - **Problem**: Browser sends WebM/Opus audio chunks, but Deepgram streaming wasn't properly configured for this format
   - **Frontend**: MediaRecorder captures audio in WebM container with Opus codec, sent as 100ms chunks over WebSocket
   - **Backend Issue**: Was trying generic `webm` format without proper streaming parameters
   - **Solution**: Configure Deepgram streaming with specific WebM/Opus parameters:
     - `audio_format="webm"` with `encoding="opus"`
     - `sample_rate=48000` (WebM standard)
     - `vad_events=True` for voice activity detection
     - `interim_results=True` for real-time feedback
     - Multiple fallback configurations for robustness
   - **Result Processing**: Enhanced to handle both interim and final results, with proper error handling and logging

7. **STT Streaming Reliability Issues (Phase 3)**: Fixed 2025-07-30c - True Deepgram WebSocket streaming proved complex and unreliable. Solution: Implemented "fake streaming" approach:
   - **Problem**: WebSocket streaming to Deepgram has connection management complexity, interim result handling issues, and unpredictable behavior
   - **Solution**: Adopted Thanotopolis's proven approach using audio buffering + Deepgram file API
   - **Implementation**: Buffer 0.5-2 seconds of audio, then send to `transcribe_chunk()` method using file API
   - **Benefits**: More reliable, simpler error handling, better debugging, consistent results
   - **Trade-off**: Slightly higher latency (0.5-2s) but much more stable transcription

8. **WebSocket Disconnection After Message Send (Phase 5)**: Fixed 2025-07-30e - WebSocket connection closed after sending chat messages, breaking subsequent speech transcription:
   - **Problem**: After sending a message, WebSocket would close and audio processor would return early when detecting closed connection
   - **Root Cause**: Chat message sending process somehow closes the STT WebSocket connection
   - **Solution**: Automatic WebSocket reconnection in audio processor when audio input is detected but connection is closed
   - **Implementation**: Modified `onaudioprocess` handler to detect closed WebSocket, create new connection, preserve event handlers, and continue processing
   - **Technical Fix**: Changed `const ws` to `let ws` in ChatInterface.tsx to allow reassignment during reconnection
   - **Result**: Continuous speech transcription functionality even after sending multiple chat messages

9. **Latency Optimization & UX Flow Issues (Phase 6)**: Fixed 2025-07-30f - Multiple improvements for faster response and better user experience:
   - **Latency Issues**: First utterance took too long due to AudioContext creation, between-utterance delays from excessive buffering
   - **UX Issues**: STT would turn off during agent replies and not restart automatically, input focus lost after replies, WebSocket reconnection floods
   - **Solutions Implemented**:
     - Pre-create AudioContext on component mount with suspend/resume pattern
     - Reduced backend buffer requirements (0.75s min vs 1s, 1.75s max vs 2s, 400ms timeout vs 500ms)
     - Limited WebSocket reconnection attempts to 3 maximum with counter reset
     - Auto-restart recording after agent replies complete (both with/without TTS playback)
     - Always return focus to MessageInput after agent responses for seamless conversation
   - **Performance Improvements**: ~100-150ms faster first utterance, ~200-400ms faster between utterances
   - **UX Improvements**: Continuous hands-free conversation flow, no more manual re-enabling of STT after replies

## Testing Voice Features

1. Click mic icon to start recording
2. Speak your message - transcribed text appears in input field automatically
3. Either press Enter to send or continue speaking for additional utterances
4. Toggle speaker icon to enable/disable TTS playback
5. Assistant responses will be spoken if TTS is enabled
6. **Hands-free Mode (Phase 6)**: If recording was active before sending a message, it automatically restarts after the agent reply completes, allowing for continuous conversation without manual re-activation