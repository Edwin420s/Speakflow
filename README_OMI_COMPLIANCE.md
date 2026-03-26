# SpeakFlow - Omi AI Wearable Integration

A comprehensive conversation analysis and task extraction platform fully compliant with [Omi AI wearable](https://www.withomi.com/) documentation standards. SpeakFlow seamlessly integrates with Omi devices to provide real-time transcription, AI-powered task extraction, and conversation memory management.

## 🎯 **Omi Documentation Compliance**

SpeakFlow is built following the official Omi developer documentation and supports:

### ✅ **Core Omi Features Implemented**
- **Real-time Audio Streaming** - `/v4/listen` WebSocket endpoint for live audio processing
- **BLE Device Integration** - Official Omi BLE protocol with proper UUIDs and characteristics
- **Conversation Storage** - Firestore-compatible conversation memory and search
- **Firebase Authentication** - Full Firebase Auth, Google OAuth, and email/password support
- **Speech-to-Text Services** - Deepgram, Soniox, and Speechmatics integration
- **Conversation Memory** - Vector search and memory extraction capabilities
- **Third-party Wearables** - Support for Plaud, Limitless, and custom devices

### 📋 **API Endpoints Following Omi Standards**

#### Authentication (`/auth/*`)
- `POST /auth/firebase/login` - Firebase ID token authentication
- `POST /auth/email/login` - Email/password authentication  
- `POST /auth/refresh` - Access token refresh

#### Device Management (`/v1/devices/*`)
- `GET /v1/devices/scan` - BLE device scanning
- `POST /v1/devices/{device_id}/connect` - Device connection
- `GET /v1/devices/{device_id}/status` - Device status and battery

#### Real-time Processing (`/v4/listen`)
- WebSocket endpoint for live audio streaming
- Multi-language support with automatic STT service selection
- Real-time transcription and AI processing

#### Conversation Management (`/v1/conversations/*`)
- `GET /v1/conversations` - User conversation listing
- `GET /v1/conversations/{conversation_id}` - Conversation details
- `POST /v1/conversations/search` - Content search and filtering

## 🚀 **Quick Start**

### Prerequisites
- Python 3.11+
- Node.js 18+
- Omi AI wearable device (optional for demo)
- OpenAI API key
- Firebase project (for production auth)

### Local Development

1. **Clone and setup backend:**
   ```bash
   cd Server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   OPENAI_API_KEY=your_openai_key
   JWT_SECRET_KEY=your_jwt_secret
   ```

3. **Run backend server:**
   ```bash
   python main.py
   ```

4. **Setup frontend:**
   ```bash
   cd Client
   npm install
   npm run dev
   ```

5. **Access the application:**
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## 🔧 **Omi Device Integration**

### Supported Devices
- **Omi DevKit 2** - Full BLE integration with OPUS codec
- **Omi Glass** - Smart glasses with audio capture
- **Third-party** - Plaud, Limitless, and custom BLE devices

### BLE Protocol Implementation
```python
# Official Omi BLE Service UUIDs
OMI_AUDIO_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"
OMI_DEVICE_INFO_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"
OMI_BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
```

### Audio Streaming Support
- **Codecs**: OPUS, PCM, MULAW, AAC
- **Sample Rates**: 8kHz, 16kHz, 44.1kHz
- **Real-time Processing**: WebSocket-based streaming

## 📊 **Conversation Memory System**

SpeakFlow implements Omi's conversation storage architecture:

### Data Structure
```typescript
interface Conversation {
  id: string;
  created_at: Date;
  started_at: Date;
  finished_at: Date;
  source: 'omi' | 'phone' | 'desktop' | 'openglass';
  language: string;
  status: 'in_progress' | 'processing' | 'completed';
  structured: {
    title: string;
    overview: string;
    category: string;
    action_items: ActionItem[];
    events: Event[];
    memories: Memory[];
  };
  transcript_segments: TranscriptSegment[];
}
```

### Memory Extraction
- **Action Items**: Tasks with assignments and deadlines
- **Events**: Calendar events and meetings
- **Memories**: Key facts and context for future reference

## 🤖 **AI Processing Pipeline**

### Task Extraction
- OpenAI GPT-4 integration with Kenyan business context
- Structured JSON output with tasks, priorities, and assignments
- Custom prompts for African business environments

### Real-time Features
- Live transcription streaming
- Progressive task extraction
- Instant summary generation

## 🔐 **Authentication & Security**

### Firebase Integration
- Firebase Auth token verification
- Google OAuth support
- Custom email/password authentication

### API Security
- JWT-based access tokens
- Refresh token rotation
- Rate limiting per endpoint
- CORS configuration

## 🌍 **Localization & Context**

### Kenyan Business Focus
- Local business terminology (M-Pesa, Safaricom, KCB, Equity Bank)
- Cultural context awareness
- Local time zone and currency support

### Multi-language Support
- English (primary)
- Swahili phrases recognition
- Automatic language detection

## 📱 **Mobile Compatibility**

### Progressive Web App
- Responsive design for mobile devices
- Offline conversation caching
- Push notification support

### Native App Ready
- RESTful API for mobile apps
- WebSocket support for real-time features
- OAuth integration for third-party apps

## 🔗 **External Integrations**

### Current Integrations
- **Trello** - Task management and card creation
- **WhatsApp** - Summary notifications via Twilio
- **Google Calendar** - Event scheduling (planned)

### Extensible Architecture
- Plugin system for new integrations
- Webhook support for external services
- API-first design for third-party apps

## 📈 **Monitoring & Analytics**

### Usage Tracking
- API call logging and analytics
- Conversation processing metrics
- Device connection statistics

### Health Monitoring
- Multiple health check endpoints
- Service status monitoring
- Error tracking and alerting

## 🐳 **Docker Deployment**

### Production Setup
```bash
# Using Docker Compose
docker-compose up -d

# Individual services
docker build -t speakflow-api .
docker run -p 8000:8000 --env-file .env speakflow-api
```

### Environment Variables
```env
# Required
OPENAI_API_KEY=your_openai_key
JWT_SECRET_KEY=your_jwt_secret
DATABASE_URL=postgresql://user:pass@localhost/speakflow

# Optional
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
```

## 🧪 **Testing**

### Backend Tests
```bash
cd Server
pytest test_main.py -v
pytest --cov=. --cov-report=html test_main.py
```

### Demo Scenarios
```bash
python demo_kenyan_scenarios.py
```

## 📚 **API Documentation**

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🤝 **Contributing to Omi Compliance**

When contributing to SpeakFlow, ensure:
1. Follow Omi documentation standards
2. Maintain BLE protocol compatibility
3. Test with actual Omi devices
4. Update documentation for new features

## 📄 **License**

This project is licensed under the MIT License.

## 🆘 **Support**

For Omi-specific issues:
- [Omi Developer Documentation](https://docs.withomi.com/)
- [Omi GitHub](https://github.com/basedhardware/omi)
- Create an issue in this repository

---

**Built with ❤️ for the Omi ecosystem**
