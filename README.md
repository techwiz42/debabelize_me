# 🗣️ Debabelize Me

**AI-Powered Voice Chat Application with Universal Language Processing**

A modern web application that combines conversational AI with advanced voice processing capabilities, powered by the Debabelizer library for universal speech-to-text (STT) and text-to-speech (TTS) operations.

## 🌟 Features

### 🤖 **Meet Babs - Your Witty AI Assistant**
- **Conversational AI**: Powered by OpenAI's GPT-4o-mini with a friendly, witty personality
- **Web Search Integration**: Real-time information retrieval via Google Custom Search API
- **Multi-language Support**: Responds in 15+ languages including Spanish, French, German, Japanese, and more
- **Context Awareness**: Maintains conversation history for natural, flowing discussions

### 🎙️ **Advanced Voice Processing**
- **Speech-to-Text**: Powered by OpenAI Whisper for accurate transcription
- **Text-to-Speech**: High-quality voice synthesis using OpenAI TTS
- **Real-time Streaming**: WebSocket-based streaming for low-latency voice interactions
- **Multi-format Support**: Handles various audio formats (WebM, WAV, MP3, etc.)

### 🌐 **Modern Web Interface**
- **Responsive Design**: Clean, modern chat interface built with Next.js and TypeScript
- **Real-time Updates**: Instant message delivery and typing indicators
- **Audio Controls**: Integrated microphone and speaker controls
- **Cross-platform**: Works on desktop and mobile devices

### 🔧 **Technical Excellence**
- **FastAPI Backend**: High-performance async API with automatic documentation
- **WebSocket Support**: Real-time bidirectional communication
- **Error Handling**: Robust error handling with fallback mechanisms
- **CORS Enabled**: Secure cross-origin resource sharing
- **Environment-based Configuration**: Easy deployment and configuration management

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │   AI Services   │
│   (Next.js)     │◄───┤    (FastAPI)     │◄───┤   (OpenAI)      │
│                 │    │                  │    │                 │
│ • Chat UI       │    │ • REST APIs      │    │ • GPT-4o-mini   │
│ • Voice Controls│    │ • WebSocket      │    │ • Whisper STT   │
│ • TypeScript    │    │ • Debabelizer    │    │ • OpenAI TTS    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📦 Project Structure

```
debabelize_me/
├── frontend/              # Next.js React frontend
│   ├── app/              # App router pages
│   ├── components/       # React components
│   │   ├── ChatInterface.tsx
│   │   ├── MessageInput.tsx
│   │   └── MessageItem.tsx
│   ├── services/         # API services
│   │   └── api.ts
│   ├── package.json
│   └── tsconfig.json
│
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py # Configuration settings
│   │   └── main.py       # FastAPI application
│   ├── requirements.txt
│   └── run.py
│
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ for frontend development
- **Python** 3.8+ for backend development
- **OpenAI API Key** for AI and voice services
- **Google Custom Search API** (optional, for web search functionality)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   # Create .env file in backend directory
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   
   # Optional: Add Google Search API for web search functionality
   echo "GOOGLE_API_KEY=your_google_api_key" >> .env
   echo "GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id" >> .env
   ```

4. **Run the backend server**:
   ```bash
   python -m uvicorn app.main:app --reload --port 8005 --host 0.0.0.0
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment** (if different from default):
   ```bash
   # Create .env.local file if using different backend URL
   echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8005" > .env.local
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```

5. **Open your browser**:
   - Frontend: http://localhost:3005
   - API Documentation: http://localhost:8005/docs

## 🔧 API Endpoints

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send text message to Babs AI assistant |
| `POST` | `/stt` | Convert audio file to text |
| `POST` | `/tts` | Convert text to speech audio |
| `POST` | `/clear-conversation` | Clear conversation history |
| `GET` | `/health` | Health check endpoint |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `WS /ws/chat` | Streaming chat responses |
| `WS /ws/stt` | Real-time speech-to-text |

### Example API Usage

#### Text Chat
```bash
curl -X POST "http://localhost:8005/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Babs! How are you today?",
    "language": "en"
  }'
```

#### Speech-to-Text
```bash
curl -X POST "http://localhost:8005/stt" \
  -F "audio=@recording.wav"
```

#### Text-to-Speech
```bash
curl -X POST "http://localhost:8005/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! This is Babs speaking.",
    "voice": "alloy"
  }' \
  --output speech.mp3
```

## 🌍 Multi-language Support

Babs can communicate in multiple languages:

- **English** (en) - Default
- **Spanish** (es) - Español
- **French** (fr) - Français
- **German** (de) - Deutsch
- **Italian** (it) - Italiano
- **Portuguese** (pt) - Português
- **Russian** (ru) - Русский
- **Japanese** (ja) - 日本語
- **Korean** (ko) - 한국어
- **Chinese** (zh) - 中文
- **Arabic** (ar) - العربية
- **Hindi** (hi) - हिन्दी
- **Polish** (pl) - Polski
- **Dutch** (nl) - Nederlands
- **Swedish** (sv) - Svenska
- **Turkish** (tr) - Türkçe

Simply specify the language code in your API requests or let Babs auto-detect the language from your input.

## 🔍 Web Search Integration

Babs can search the web for current information using Google Custom Search API:

1. Set up a Google Custom Search Engine at [cse.google.com](https://cse.google.com)
2. Get your API key from [Google Cloud Console](https://console.cloud.google.com)
3. Add to your `.env` file:
   ```bash
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
   ```

When you ask Babs about current events or recent information, she'll automatically search the web and provide up-to-date answers.

## 🎯 Use Cases

### Personal Assistant
- **Daily conversations** with a witty AI companion
- **Information lookup** with real-time web search
- **Multi-language practice** and translation
- **Voice interaction** for hands-free operation

### Development & Integration
- **Voice-enabled applications** using the API
- **Multi-language content creation** with TTS
- **Speech recognition** for accessibility features
- **AI chat integration** in existing applications

### Business Applications
- **Customer service bots** with personality
- **Voice-controlled interfaces** for accessibility
- **Multi-language support** for global applications
- **Real-time transcription** services

## 🛠️ Development

### Running in Development Mode

**Backend (with auto-reload)**:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8005
```

**Frontend (with hot-reload)**:
```bash
cd frontend
npm run dev
```

### Building for Production

**Frontend**:
```bash
cd frontend
npm run build
npm run start
```

**Backend**:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --workers 4
```

### Code Quality

**Frontend**:
```bash
cd frontend
npm run lint          # ESLint
npm run type-check     # TypeScript checking
```

**Backend**:
```bash
cd backend
python -m pytest      # Run tests (if available)
```

## 🚀 Deployment

### Docker Deployment (Recommended)

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8005:8005"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - GOOGLE_SEARCH_ENGINE_ID=${GOOGLE_SEARCH_ENGINE_ID}
    volumes:
      - ./backend:/app
  
  frontend:
    build: ./frontend
    ports:
      - "3005:3005"
    environment:
      - NEXT_PUBLIC_BACKEND_URL=http://backend:8005
    depends_on:
      - backend
```

### Manual Deployment

1. **Deploy Backend**:
   ```bash
   # On your server
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8005
   ```

2. **Deploy Frontend**:
   ```bash
   # Build and deploy
   cd frontend
   npm run build
   npm start
   ```

3. **Configure Reverse Proxy** (nginx example):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3005;
       }
       
       location /api {
           proxy_pass http://localhost:8005;
       }
       
       location /ws {
           proxy_pass http://localhost:8005;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

## 🧪 Testing

### Manual Testing

1. **Start both services** (backend on :8005, frontend on :3005)
2. **Open the chat interface** at http://localhost:3005
3. **Send a text message** to verify basic chat functionality
4. **Try different languages** by asking Babs to respond in Spanish, French, etc.
5. **Test web search** by asking about current events
6. **Test voice features** using the microphone and speaker buttons

### API Testing

Use the interactive API documentation at http://localhost:8005/docs to test individual endpoints.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests if applicable
4. **Run quality checks**:
   ```bash
   # Frontend
   cd frontend && npm run lint && npm run type-check
   
   # Backend
   cd backend && python -m pytest  # if tests exist
   ```
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines

- **Frontend**: Use TypeScript, follow React best practices
- **Backend**: Follow FastAPI conventions, use async/await
- **Code Style**: Use consistent formatting and meaningful variable names
- **Documentation**: Update README and API docs for new features

## 🔧 Configuration

### Environment Variables

**Backend (.env)**:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for web search)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# Optional (for CORS)
CORS_ORIGINS=["http://localhost:3005", "https://yourdomain.com"]
```

**Frontend (.env.local)**:
```bash
# Backend URL (defaults to http://localhost:8005)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8005
NEXT_PUBLIC_WS_URL=ws://localhost:8005
```

### Advanced Configuration

Check `backend/app/core/config.py` for all available configuration options including:
- CORS settings
- Voice processing parameters
- AI model configuration
- API rate limiting
- Logging levels

## 🆘 Troubleshooting

### Common Issues

**Backend won't start**:
- ✅ Check your OpenAI API key is valid
- ✅ Ensure Python 3.8+ is installed
- ✅ Install all requirements: `pip install -r requirements.txt`

**Frontend connection errors**:
- ✅ Verify backend is running on port 8005
- ✅ Check CORS configuration in backend
- ✅ Ensure `NEXT_PUBLIC_BACKEND_URL` is correct

**Voice features not working**:
- ✅ Check browser permissions for microphone access
- ✅ Verify OpenAI API key has sufficient credits
- ✅ Test with different audio formats

**WebSocket connection issues**:
- ✅ Check firewall settings for port 8005
- ✅ Verify WebSocket support in your deployment environment
- ✅ Test with different browsers

### Getting Help

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: Check the API docs at `/docs` endpoint
- **Community**: Join discussions about voice AI and language processing

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o-mini and Whisper models
- **Debabelizer Library** for universal voice processing capabilities
- **FastAPI** for the excellent Python web framework
- **Next.js** for the powerful React framework
- **Google** for Custom Search API integration

---

## 🎯 What's Next?

### Planned Features
- **Voice cloning** for personalized TTS voices
- **Real-time voice conversation** with streaming audio
- **Mobile app** for iOS and Android
- **Additional AI models** and provider support
- **Voice commands** for hands-free interaction

### Integration Opportunities
- **Smart home systems** (Alexa, Google Home)
- **Business applications** (customer service, training)
- **Educational tools** (language learning, accessibility)
- **Developer APIs** for third-party integrations

---

**Debabelize Me** - *Your intelligent voice companion, breaking down language barriers one conversation at a time* 🌍🗣️🤖