# CLAUDE.md - Project Context for Claude Code

## Project Overview
Debabelize Me is a voice-enabled chat application that leverages the **debabelizer module** for all speech-to-text (STT) and text-to-speech (TTS) functionality. The debabelizer module provides a unified, provider-agnostic interface for voice services. The app features a React/Next.js frontend and a FastAPI backend.

**Important**: All STT and TTS functionality is accessed through the debabelizer module - we do not directly integrate with providers like Deepgram or ElevenLabs. See the debabelizer documentation at `~/debabelizer/README.md` for detailed information about the module's capabilities and configuration.

**Current Status**: TTS is fully functional, while STT implementation is still in progress.

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

1. **No Localhost Fallbacks**: All URLs must come from environment variables
2. **Provider Agnostic**: Code should not hardcode specific STT/TTS providers
3. **Environment-Based Config**: All provider configuration lives in .env files
4. **WebSocket Streaming**: STT uses WebSocket for real-time transcription
5. **Audio Format**: Browser typically sends webm format for recording

## Common Issues & Solutions

1. **API Key Conflicts**: Ensure environment variables are properly set
2. **WebSocket Connection**: Check NEXT_PUBLIC_WS_URL is correctly configured
3. **Audio Permissions**: Browser requires user permission for microphone access
4. **CORS**: Backend configured to accept requests from frontend domains

## Testing Voice Features

1. Click mic icon to start recording
2. Speak your message
3. Click mic icon again to stop and send
4. Toggle speaker icon to enable/disable TTS playback
5. Assistant responses will be spoken if TTS is enabled