# 🎤 SpeakFlow

Turn conversations into actions automatically. SpeakFlow listens to meetings, extracts tasks with AI, and creates Trello cards + WhatsApp follow-ups. **Built for Omi Builder Friday hackathon - integrating with Omi AI wearable!**

## 🏆 Omi Builder Fridays Nairobi - Ready to Win!

### 🎯 Submission Information
**SpeakFlow** is specifically built for Omi Builder Fridays in Nairobi and ready for all sprint sessions:

- **📱 WhatsApp Group**: Active participant in coordination group
- **🚀 Sprint Ready**: Complete implementation for all 4 upcoming sprints
- **🤝 Collaboration Open**: Seeking team members and partnerships
- **🇰🇪 Kenya Focused**: Optimized for local business needs

### 📋 Quick Sprint Setup
```bash
# 5-minute demo setup for any sprint
git clone https://github.com/Edwin420s/speakflow.git
cd speakflow
./start-dev.sh

# Access points
Demo: https://speakflow-demo.vercel.app
API: http://localhost:8000/docs
```

### 🎤 Live Demo Capabilities
- **Real-time Omi Integration** - Device connection and processing
- **Kenyan Business Scenarios** - Fintech, M-Pesa, local contexts
- **Automated Task Extraction** - AI-powered with priority classification
- **Trello + WhatsApp Integration** - Complete workflow automation
- **Professional Dashboard** - Modern UI with live updates

### 📞 Sprint Coordination
- **WhatsApp**: +2547XXXXXXXX (Available for pairing)
- **Email**: sprint@speakflow.ai
- **GitHub**: https://github.com/your-username/speakflow
- **Demo Video**: https://youtube.com/watch?v=speakflow-demo

---

**🚀 SpeakFlow: Transform your conversations into productivity, powered by AI and Omi integration!**

*Built with ❤️ for Omi Builder Friday Nairobi - Ready to win all 4 sprints!*

## ✨ Features

- 🎤 **Live Conversation Processing** - Real-time speech-to-text analysis
- 🧠 **AI-Powered Task Extraction** - OpenAI integration optimized for Kenyan business context
- 📋 **Trello Integration** - Automatic task card creation
- 💬 **WhatsApp Follow-ups** - Smart summary generation with Kenyan business formatting
- 🔐 **API Authentication** - Secure API key management
- 📊 **Usage Analytics** - Track API usage and performance
- 🎨 **Beautiful UI** - Modern React dashboard with animations
- 🎤 **Omi AI Wearable Integration** - Real-time device connection and processing
- 🇰🇪 **Kenyan Business Context** - Optimized for African business scenarios

## 🚀 New: Omi Device Integration

### Omi Builder Friday Hackathon Features

- **🎤 Real-time Omi Connection** - Connect and process conversations from Omi AI wearable
- **📱 Live Demo Stream** - Simulated Omi device conversations for demo
- **🇰🇪 Kenyan Business Scenarios** - Fintech, M-Pesa, local bank integration examples
- **🔗 Webhook Support** - Handle real-time conversation data from Omi devices
- **📊 Device Status Monitoring** - Track Omi device connection and processing status

### Omi Integration Endpoints

```bash
# Connect to Omi device
POST /api/omi/connect

# Get device status
GET /api/omi/status

# Start demo stream
POST /api/omi/demo-stream

# Handle Omi webhook
POST /api/omi/webhook
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   External      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • AI Processing │    │ • OpenAI        │
│ • Animations    │    │ • Task Extraction│    │ • Trello         │
│ • Real-time UI  │    │ • API Auth      │    │ • WhatsApp       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- OpenAI API Key (optional for demo)

### 1. Clone & Setup

```bash
git clone <repository-url>
cd speakflow
```

### 2. Backend Setup

```bash
cd Server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
cd ../Client
npm install
cp .env.example .env.local
# Edit .env.local with your API URL
```

### 4. Start Development

```bash
# From project root
./start-dev.sh
```

Or start manually:

```bash
# Terminal 1 - Backend
cd Server
source venv/bin/activate
python main.py

# Terminal 2 - Frontend
cd Client
npm run dev
```

### 5. Access

- 🌐 Frontend: http://localhost:5173
- 📡 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

## 🔧 Configuration

### Backend (.env)

```env
# OpenAI (Required for AI processing)
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4

# Trello (Optional)
TRELLO_ENABLED=true
TRELLO_API_KEY=your-trello-key
TRELLO_TOKEN=your-trello-token
TRELLO_LIST_ID=your-list-id

# WhatsApp (Optional)
WHATSAPP_ENABLED=true
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+2547XXXXXXXX
```

### Frontend (.env.local)

```env
VITE_API_URL=http://localhost:8000
VITE_API_KEY=sk-your-api-key
```

## 📡 API Usage

### Analyze Conversation

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "John will finish the backend by Friday"}'
```

### Create Trello Card

```bash
curl -X POST "http://localhost:8000/api/trello/create" \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"task": "Finish backend", "assigned_to": "John"}'
```

### Send WhatsApp Message

```bash
curl -X POST "http://localhost:8000/api/whatsapp/send" \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Meeting summary here..."}'
```

## 🎯 Demo Flow

1. **Start Live Conversation** - Dashboard shows simulated conversation
2. **AI Processing** - Conversation is analyzed for tasks
3. **Task Extraction** - Tasks appear in real-time
4. **Trello Integration** - Click "Send to Trello" to create cards
5. **WhatsApp Summary** - Auto-generated summary ready to send

## 🔐 API Authentication

SpeakFlow uses Bearer token authentication:

1. Generate API keys via admin endpoint
2. Include in request headers: `Authorization: Bearer sk-your-key`
3. Keys support expiry and usage tracking

## 📊 Monitoring

- Health check: `/health`
- API usage logs stored in database
- Rate limiting applied to all endpoints
- Structured logging with JSON output

## 🛠️ Development

### Project Structure

```
speakflow/
├── Server/                 # Backend API
│   ├── main.py            # FastAPI application
│   ├── ai_processor.py    # OpenAI integration
│   ├── trello_integration.py
│   ├── whatsapp_integration.py
│   ├── models.py          # Pydantic models
│   ├── auth.py            # Authentication
│   ├── database.py        # Database setup
│   └── prompts/           # AI prompts
├── Client/                 # Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   └── services/      # API services
│   └── package.json
└── start-dev.sh           # Development script
```

### Adding New Integrations

1. Create integration module in `Server/`
2. Add configuration to `config.py`
3. Create API endpoints in `main.py`
4. Add frontend service in `Client/src/services/`
5. Update UI components

## 🚀 Production Deployment

### Backend

```bash
# Using Docker
docker build -t speakflow-api .
docker run -p 8000:8000 speakflow-api

# Using Python
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend

```bash
npm run build
# Deploy dist/ folder to your hosting service
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file

## 🙋‍♂️ Support

- 📧 Email: support@speakflow.ai
- 💬 Discord: [Join our community]
- 📖 Docs: [Documentation link]

## 🎉 Hackathon Project

Built for Omi Builder Friday - turning conversations from Omi AI wearable into productive actions!
