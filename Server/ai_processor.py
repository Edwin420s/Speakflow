import json
import re
import structlog
from openai import OpenAI
from typing import Dict, Any

from config import OPENAI_API_KEY, OPENAI_MODEL

logger = structlog.get_logger()

# Initialize OpenAI client lazily
_client = None

def get_openai_client():
    global _client
    if _client is None and OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

def load_prompt_template() -> str:
    """Read the prompt template from file."""
    try:
        with open("prompts/task_extraction.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("Prompt template file not found")
        raise
    except Exception as e:
        logger.error("Error reading prompt template", error=str(e))
        raise

def extract_tasks_and_summary(transcript: str) -> Dict[str, Any]:
    """
    Call OpenAI to extract tasks and summary from the transcript.
    Returns a dict with keys 'tasks' (list) and 'summary' (str).
    """
    if not transcript or not transcript.strip():
        logger.warning("Empty transcript provided")
        return {"tasks": [], "summary": "No transcript provided.", "confidence_score": 0.0}
    
    # Check if OpenAI API key is available and properly configured
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-..." or OPENAI_API_KEY.startswith("sk-..."):
        logger.warning("OpenAI API key not configured, returning mock response")
        return {
            "tasks": [
                {
                    "task": "Review transcript setup", 
                    "assigned_to": "Admin", 
                    "deadline": "ASAP", 
                    "priority": "high",
                    "status": "pending",
                    "tags": ["setup", "admin"],
                    "estimated_time": "30 minutes",
                    "context": "Initial setup review required"
                },
                {
                    "task": "Configure OpenAI API key", 
                    "assigned_to": "Admin", 
                    "deadline": "ASAP", 
                    "priority": "urgent",
                    "status": "pending",
                    "tags": ["configuration", "api"],
                    "estimated_time": "15 minutes",
                    "context": "API key configuration for AI processing"
                }
            ],
            "summary": "Mock response: Please configure OpenAI API key for real AI processing.",
            "confidence_score": 0.5
        }
    
    try:
        template = load_prompt_template()
        prompt = template.replace("{transcript}", transcript)

        client = get_openai_client()
        if not client:
            raise Exception("Failed to initialize OpenAI client")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts action items from meeting conversations. Return tasks with priority levels (urgent/high/medium/low), status (pending/in_progress), estimated time, and relevant tags."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200  # Increased to support enhanced schema
        )

        content = response.choices[0].message.content

        # Try to extract JSON from the response (the model may wrap it in markdown)
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            content = json_match.group()

        try:
            result = json.loads(content)
            # Validate the structure
            if not isinstance(result, dict) or "tasks" not in result or "summary" not in result:
                raise ValueError("Invalid response structure")
            
            # Ensure tasks is a list
            if not isinstance(result["tasks"], list):
                result["tasks"] = []
            
            # Enhance tasks with default values for new fields
            for task in result["tasks"]:
                if "priority" not in task:
                    # Determine priority based on content
                    task_text = task.get("task", "").lower()
                    if any(urgent_word in task_text for urgent_word in ["urgent", "asap", "immediately", "critical"]):
                        task["priority"] = "urgent"
                    elif any(high_word in task_text for high_word in ["important", "priority", "soon", "quickly"]):
                        task["priority"] = "high"
                    elif any(low_word in task_text for low_word in ["later", "sometime", "eventually", "low"]):
                        task["priority"] = "low"
                    else:
                        task["priority"] = "medium"
                
                if "status" not in task:
                    task["status"] = "pending"
                
                if "tags" not in task:
                    task["tags"] = []
                
                if "estimated_time" not in task:
                    # Estimate time based on task complexity
                    task_length = len(task.get("task", ""))
                    if task_length > 100:
                        task["estimated_time"] = "2-4 hours"
                    elif task_length > 50:
                        task["estimated_time"] = "1-2 hours"
                    else:
                        task["estimated_time"] = "30-60 minutes"
                
                if "context" not in task:
                    task["context"] = f"Task extracted from meeting transcript"
            
            # Calculate confidence score based on response quality
            confidence_score = min(1.0, len(result["tasks"]) * 0.1 + 0.5)  # Simple heuristic
            result["confidence_score"] = confidence_score
            
            logger.info("Successfully processed transcript", tasks_count=len(result["tasks"]), confidence_score=confidence_score)
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), content=content)
            return {"tasks": [], "summary": "Could not parse AI response. Please try again.", "confidence_score": 0.0}
        except ValueError as e:
            logger.error("Invalid response structure", error=str(e))
            return {"tasks": [], "summary": "Invalid response format from AI.", "confidence_score": 0.0}

    except Exception as e:
        logger.error("Error processing transcript with OpenAI", error=str(e))
        return {"tasks": [], "summary": f"Error processing transcript: {str(e)}", "confidence_score": 0.0}