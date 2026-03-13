import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from main import app
from models import Task, TranscriptRequest, SpeakFlowResponse
from database import get_database, init_database
from auth import AuthManager

client = TestClient(app)

class TestMainEndpoints:
    """Test main API endpoints."""
    
    def test_root_endpoint(self):
        """Test the root health check endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "SpeakFlow backend is running"
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_health_endpoint(self):
        """Test the detailed health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "openai" in data["services"]
        assert "timestamp" in data
    
    def test_analyze_endpoint_empty_text(self):
        """Test analyze endpoint with empty text."""
        response = client.post("/api/analyze", json={"text": ""})
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert "empty" in data["detail"]["error"].lower()
    
    def test_analyze_endpoint_short_text(self):
        """Test analyze endpoint with text shorter than minimum."""
        response = client.post("/api/analyze", json={"text": "Hi"})
        assert response.status_code == 422
        data = response.json()
        assert "error" in data["detail"]
    
    @patch('ai_processor.extract_tasks_and_summary')
    def test_analyze_endpoint_success(self, mock_extract):
        """Test analyze endpoint with valid input."""
        # Mock the AI processor response
        mock_extract.return_value = {
            "tasks": [
                {"task": "Test task", "assigned_to": "John", "deadline": "Friday"}
            ],
            "summary": "Test meeting summary"
        }
        
        response = client.post("/api/analyze", json={"text": "This is a test transcript with enough content to pass validation."})
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "summary" in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["task"] == "Test task"
        assert data["summary"] == "Test meeting summary"
    
    @patch('ai_processor.extract_tasks_and_summary')
    def test_analyze_endpoint_ai_error(self, mock_extract):
        """Test analyze endpoint when AI processing fails."""
        # Mock the AI processor to raise an exception
        mock_extract.side_effect = Exception("AI processing failed")
        
        response = client.post("/api/analyze", json={"text": "This is a test transcript with enough content to pass validation."})
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"]

class TestModels:
    """Test Pydantic models."""
    
    def test_task_model_valid(self):
        """Test valid Task model."""
        task = Task(task="Complete project", assigned_to="Alice", deadline="2024-01-15")
        assert task.task == "Complete project"
        assert task.assigned_to == "Alice"
        assert task.deadline == "2024-01-15"
    
    def test_task_model_empty_task(self):
        """Test Task model with empty task."""
        with pytest.raises(ValueError):
            Task(task="", assigned_to="Alice", deadline="2024-01-15")
    
    def test_transcript_request_valid(self):
        """Test valid TranscriptRequest model."""
        request = TranscriptRequest(text="This is a valid transcript with enough content.")
        assert request.text == "This is a valid transcript with enough content."
    
    def test_transcript_request_short_text(self):
        """Test TranscriptRequest with text too short."""
        with pytest.raises(ValueError):
            TranscriptRequest(text="Short")
    
    def test_speakflow_response_valid(self):
        """Test valid SpeakFlowResponse model."""
        tasks = [Task(task="Task 1"), Task(task="Task 2")]
        response = SpeakFlowResponse(tasks=tasks, summary="Meeting summary")
        assert len(response.tasks) == 2
        assert response.summary == "Meeting summary"

class TestAIProcessor:
    """Test AI processing functionality."""
    
    @patch('ai_processor.client.chat.completions.create')
    def test_extract_tasks_and_summary_success(self, mock_completion):
        """Test successful task and summary extraction."""
        from ai_processor import extract_tasks_and_summary
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"tasks": [{"task": "Test task"}], "summary": "Test summary"}'
        mock_completion.return_value = mock_response
        
        result = extract_tasks_and_summary("Test transcript")
        assert "tasks" in result
        assert "summary" in result
        assert len(result["tasks"]) == 1
        assert result["summary"] == "Test summary"
    
    @patch('ai_processor.client.chat.completions.create')
    def test_extract_tasks_and_summary_invalid_json(self, mock_completion):
        """Test handling of invalid JSON response."""
        from ai_processor import extract_tasks_and_summary
        
        # Mock OpenAI response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_completion.return_value = mock_response
        
        result = extract_tasks_and_summary("Test transcript")
        assert result["tasks"] == []
        assert "Could not parse" in result["summary"]
    
    def test_extract_tasks_and_summary_empty_input(self):
        """Test handling of empty transcript input."""
        from ai_processor import extract_tasks_and_summary
        
        result = extract_tasks_and_summary("")
        assert result["tasks"] == []
        assert result["summary"] == "No transcript provided."

class TestTrelloIntegration:
    """Test Trello integration functionality."""
    
    @patch('trello_integration.validate_trello_credentials')
    def test_create_trello_cards_no_credentials(self, mock_validate):
        """Test Trello card creation without credentials."""
        from trello_integration import create_trello_cards
        
        mock_validate.return_value = False
        
        tasks = [{"task": "Test task"}]
        result = create_trello_cards(tasks)
        assert len(result) == 1
        assert result[0].error == "Trello credentials not configured"
    
    @patch('trello_integration.validate_trello_credentials')
    @patch('requests.post')
    def test_create_trello_cards_success(self, mock_post, mock_validate):
        """Test successful Trello card creation."""
        from trello_integration import create_trello_cards
        
        mock_validate.return_value = True
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "card123", "name": "Test task"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        tasks = [{"task": "Test task", "assigned_to": "John", "deadline": "Friday"}]
        result = create_trello_cards(tasks)
        
        assert len(result) == 1
        assert result[0].id == "card123"
        assert result[0].name == "Test task"
        assert result[0].error is None
        assert "trello.com/c/card123" in result[0].url

class TestWhatsAppIntegration:
    """Test WhatsApp integration functionality."""
    
    @patch('whatsapp_integration.validate_twilio_credentials')
    def test_send_whatsapp_message_no_credentials(self, mock_validate):
        """Test WhatsApp message sending without credentials."""
        from whatsapp_integration import send_whatsapp_message
        
        mock_validate.return_value = False
        
        result = send_whatsapp_message("Test message")
        assert result.status == "failed"
        assert "credentials" in result.error.lower()
    
    @patch('whatsapp_integration.validate_twilio_credentials')
    @patch('whatsapp_integration.Client')
    def test_send_whatsapp_message_success(self, mock_client, mock_validate):
        """Test successful WhatsApp message sending."""
        from whatsapp_integration import send_whatsapp_message
        
        mock_validate.return_value = True
        
        # Mock Twilio client and message
        mock_message = MagicMock()
        mock_message.sid = "msg123"
        mock_message.status = "queued"
        
        mock_twilio_client = MagicMock()
        mock_twilio_client.messages.create.return_value = mock_message
        mock_client.return_value = mock_twilio_client
        
        result = send_whatsapp_message("Test message")
        
        assert result.message_sid == "msg123"
        assert result.status == "queued"
        assert result.error is None
    
    def test_send_whatsapp_message_empty(self):
        """Test WhatsApp message sending with empty message."""
        from whatsapp_integration import send_whatsapp_message
        
        result = send_whatsapp_message("")
        assert result.status == "failed"
        assert "empty" in result.error.lower()
    
    def test_format_whatsapp_summary(self):
        """Test WhatsApp message formatting."""
        from whatsapp_integration import format_whatsapp_summary
        
        message = format_whatsapp_summary("Meeting discussed project timeline", 3)
        assert "📝" in message
        assert "Meeting discussed project timeline" in message
        assert "📋" in message
        assert "3 task(s) extracted" in message

class TestAuth:
    """Test authentication functionality."""
    
    def test_generate_api_key(self):
        """Test API key generation."""
        auth_manager = AuthManager()
        api_key = auth_manager.generate_api_key()
        assert api_key.startswith("sk-")
        assert len(api_key) > 40
    
    def test_hash_api_key(self):
        """Test API key hashing."""
        auth_manager = AuthManager()
        api_key = "sk-test123"
        hashed = auth_manager.hash_api_key(api_key)
        
        # Same key should produce same hash
        assert auth_manager.hash_api_key(api_key) == hashed
        
        # Different key should produce different hash
        assert auth_manager.hash_api_key("sk-different") != hashed

class TestDatabase:
    """Test database functionality."""
    
    def test_database_initialization(self):
        """Test database initialization."""
        db = get_database()
        assert db is not None
        assert db.engine is not None
        assert db.SessionLocal is not None
    
    def test_session_creation(self):
        """Test database session creation."""
        db = get_database()
        session = db.get_session()
        assert session is not None
        session.close()

# Integration tests
class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @patch('ai_processor.extract_tasks_and_summary')
    @patch('trello_integration.create_trello_cards')
    @patch('whatsapp_integration.send_whatsapp_message')
    def test_full_workflow_success(self, mock_whatsapp, mock_trello, mock_ai):
        """Test the complete workflow with all services enabled."""
        # Mock AI processing
        mock_ai.return_value = {
            "tasks": [
                {"task": "Complete backend", "assigned_to": "Dev", "deadline": "2024-01-20"}
            ],
            "summary": "Team discussed backend development"
        }
        
        # Mock Trello integration
        mock_trello.return_value = []
        
        # Mock WhatsApp integration
        mock_whatsapp.return_value = MagicMock(status="sent")
        
        # Test the analyze endpoint
        response = client.post("/api/analyze", json={
            "text": "Meeting transcript about backend development. Dev will complete the backend by January 20th."
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["summary"] == "Team discussed backend development"
        
        # Verify all services were called
        mock_ai.assert_called_once()
        mock_trello.assert_called_once()
        mock_whatsapp.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
