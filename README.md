# Debabelize Me Backend

FastAPI backend for the voice-enabled chat application with speech-to-text (STT) and text-to-speech (TTS) capabilities.

## Features

- **Speech-to-Text**: Real-time audio streaming with language auto-detection
- **Text-to-Speech**: Multi-language voice output
- **AI Chat**: OpenAI GPT-4o-mini integration with streaming responses
- **WebSocket Support**: Low-latency real-time communication
- **Multi-language**: Supports 13+ languages for both input and output

## API Endpoints

### REST Endpoints
- `POST /chat` - Text-based chat with conversation history
- `POST /stt` - Speech-to-text (file upload)
- `POST /tts` - Text-to-speech (returns audio)
- `POST /clear-conversation` - Clear conversation history
- `GET /health` - Health check

### WebSocket Endpoints
- `WS /ws/stt` - Streaming speech-to-text
- `WS /ws/chat` - Streaming chat responses

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Run the server**:
   ```bash
   python -m uvicorn app.main:app --reload --port 8005
   ```

4. **Access the API**:
   - Server: http://localhost:8005
   - Docs: http://localhost:8005/docs

## Environment Variables

Required environment variables in `.env`:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Dependencies

- **FastAPI**: Web framework with automatic API documentation
- **uvicorn**: ASGI server for production
- **openai**: OpenAI API client
- **pydantic-settings**: Configuration management
- **websockets**: WebSocket support
- **httpx**: HTTP client for API calls

## Architecture

- **Debabelizer Integration**: Uses the debabelizer library for STT/TTS processing
- **WebSocket Streaming**: Real-time audio and text streaming
- **Conversation Memory**: Maintains context across messages
- **Provider Support**: Whisper (STT) and OpenAI (TTS) with extensible provider system

## Development

### Running in Development
```bash
python -m uvicorn app.main:app --reload --port 8005 --host 0.0.0.0
```

### Project Structure
```
backend/
├── app/
│   ├── core/
│   │   └── config.py      # Configuration settings
│   └── main.py            # FastAPI application
├── debabelizer/           # STT/TTS library
├── requirements.txt
├── .env                   # Environment variables
└── README.md
```

## Configuration

The application uses pydantic-settings for configuration management. See `app/core/config.py` for available settings.

## Production Deployment

For production deployment, use a production ASGI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8005 --workers 4
```

Consider using nginx as a reverse proxy for WebSocket support and SSL termination.

## Troubleshooting

- **WebSocket connection issues**: Check firewall settings and ensure port 8005 is accessible
- **Audio processing errors**: Verify OpenAI API key is valid and has sufficient credits
- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

## License

Part of the Debabelize Me voice chat application.