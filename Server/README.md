# SpeakFlow Backend API

A FastAPI-based backend service for analyzing conversation transcripts and extracting actionable tasks using AI.

## Features

- **AI-Powered Analysis**: Uses OpenAI GPT models to extract tasks and summaries from conversation transcripts
- **Task Management**: Automatically creates Trello cards from extracted tasks
- **WhatsApp Integration**: Sends meeting summaries via WhatsApp using Twilio
- **Authentication**: API key-based authentication with usage tracking
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Comprehensive Logging**: Structured logging with detailed error tracking
- **Health Monitoring**: Multiple health check endpoints
- **Database Persistence**: PostgreSQL/SQLite support for data storage
- **Docker Support**: Full containerization with Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional, for containerized deployment)
- OpenAI API key
- Trello API credentials (optional)
- Twilio credentials (optional)

### Local Development

1. **Clone and setup:**
   ```bash
   cd Server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys and configuration
   ```

3. **Initialize database:**
   ```bash
   python -c "from database import init_database; init_database()"
   ```

4. **Run the server:**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Using Docker Compose (recommended):**
   ```bash
   docker-compose up -d
   ```

2. **Using Docker directly:**
   ```bash
   docker build -t speakflow-api .
   docker run -p 8000:8000 --env-file .env speakflow-api
   ```

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Environment Variables

### Required
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: Database connection string (default: SQLite)

### Optional
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4)
- `TRELLO_ENABLED`: Enable Trello integration (true/false)
- `TRELLO_API_KEY`: Trello API key
- `TRELLO_TOKEN`: Trello API token
- `TRELLO_LIST_ID`: Trello list ID for card creation
- `WHATSAPP_ENABLED`: Enable WhatsApp integration (true/false)
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_WHATSAPP_FROM`: Twilio WhatsApp number
- `WHATSAPP_TO`: Recipient WhatsApp number
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `REDIS_URL`: Redis connection URL for rate limiting
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

## API Endpoints

### Health Checks
- `GET /` - Basic health check
- `GET /health` - Detailed health check with service status

### Main API
- `POST /api/analyze` - Analyze conversation transcript

#### Request Body
```json
{
  "text": "Conversation transcript text to analyze..."
}
```

#### Response
```json
{
  "tasks": [
    {
      "task": "Complete backend development",
      "assigned_to": "John Doe",
      "deadline": "2024-01-15"
    }
  ],
  "summary": "The team discussed backend development tasks..."
}
```

## Testing

Run the test suite:
```bash
pytest test_main.py -v
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html test_main.py
```

## Architecture

### Core Components

1. **main.py**: FastAPI application with middleware and endpoints
2. **ai_processor.py**: OpenAI integration for text analysis
3. **trello_integration.py**: Trello API integration
4. **whatsapp_integration.py**: Twilio WhatsApp integration
5. **auth.py**: Authentication and API key management
6. **database.py**: Database models and connection management
7. **models.py**: Pydantic models for request/response validation

### Security Features

- API key authentication
- Rate limiting per IP and endpoint
- Input validation and sanitization
- CORS configuration
- Request/response logging
- Error handling without information leakage

### Database Schema

- **transcripts**: Store conversation transcripts
- **tasks**: Extracted tasks with metadata
- **api_keys**: Authentication key management
- **usage_logs**: API usage tracking and analytics

## Monitoring and Logging

The application uses structured logging with JSON output. Logs include:
- Request metadata (IP, user agent, timing)
- Error details with stack traces
- External service integration results
- Performance metrics

## Rate Limiting

Default rate limits:
- `/api/analyze`: 5 requests per minute per IP
- `/health`: 30 requests per minute per IP
- `/`: 10 requests per minute per IP

## Deployment Considerations

### Production Checklist

1. **Security**
   - Use HTTPS in production
   - Configure proper CORS origins
   - Set strong JWT secret keys
   - Regularly rotate API keys

2. **Database**
   - Use PostgreSQL in production
   - Set up proper backups
   - Configure connection pooling

3. **Performance**
   - Enable Redis for rate limiting
   - Configure appropriate timeouts
   - Monitor memory usage

4. **Monitoring**
   - Set up log aggregation
   - Monitor health endpoints
   - Track API usage metrics

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Check API key validity
   - Verify model availability
   - Monitor rate limits

2. **Database Connection Issues**
   - Verify connection string
   - Check network connectivity
   - Ensure proper permissions

3. **Rate Limiting Issues**
   - Check Redis connectivity
   - Verify limit configurations
   - Monitor IP-based limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation
- Review the troubleshooting guide
