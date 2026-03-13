import json
import re
import structlog
from openai import OpenAI
from typing import Dict, Any

from config import OPENAI_API_KEY, OPENAI_MODEL

logger = structlog.get_logger()

client = OpenAI(api_key=OPENAI_API_KEY)

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
        return {"tasks": [], "summary": "No transcript provided."}
    
    try:
        template = load_prompt_template()
        prompt = template.replace("{transcript}", transcript)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts action items from meeting conversations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
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
            
            logger.info("Successfully processed transcript", tasks_count=len(result["tasks"]))
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), content=content)
            return {"tasks": [], "summary": "Could not parse AI response. Please try again."}
        except ValueError as e:
            logger.error("Invalid response structure", error=str(e))
            return {"tasks": [], "summary": "Invalid response format from AI."}

    except Exception as e:
        logger.error("Error processing transcript with OpenAI", error=str(e))
        return {"tasks": [], "summary": f"Error processing transcript: {str(e)}"}