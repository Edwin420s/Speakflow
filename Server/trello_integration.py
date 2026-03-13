import requests
import structlog
from typing import List, Dict, Any
from models import Task, TrelloCardResponse

from config import TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_LIST_ID

logger = structlog.get_logger()

def validate_trello_credentials() -> bool:
    """Validate that required Trello credentials are present."""
    missing = []
    if not TRELLO_API_KEY:
        missing.append("TRELLO_API_KEY")
    if not TRELLO_TOKEN:
        missing.append("TRELLO_TOKEN")
    if not TRELLO_LIST_ID:
        missing.append("TRELLO_LIST_ID")
    
    if missing:
        logger.error("Missing Trello credentials", missing=missing)
        return False
    return True

def create_trello_cards(tasks: List[Dict[str, Any]]) -> List[TrelloCardResponse]:
    """
    Create a Trello card for each task in the provided list.
    
    Args:
        tasks: List of task dictionaries containing task details
        
    Returns:
        List of TrelloCardResponse objects with creation results
    """
    if not validate_trello_credentials():
        logger.warning("Trello credentials missing, skipping card creation")
        return [TrelloCardResponse(
            id="",
            name="Credential Error",
            error="Trello credentials not configured"
        )]
    
    if not tasks:
        logger.info("No tasks to create Trello cards for")
        return []
    
    url = "https://api.trello.com/1/cards"
    responses = []
    
    for i, task in enumerate(tasks):
        try:
            # Validate task structure
            if not isinstance(task, dict) or "task" not in task:
                logger.warning("Invalid task structure", task_index=i, task=task)
                responses.append(TrelloCardResponse(
                    id="",
                    name="Invalid Task",
                    error="Invalid task structure"
                ))
                continue
            
            name = task.get("task", "Untitled task").strip()
            if not name:
                name = "Untitled task"
            
            # Build description
            desc_parts = []
            assigned_to = task.get("assigned_to")
            if assigned_to and assigned_to.strip():
                desc_parts.append(f"Assigned to: {assigned_to.strip()}")
            
            deadline = task.get("deadline")
            if deadline and deadline.strip():
                desc_parts.append(f"Deadline: {deadline.strip()}")
            
            desc = "\n".join(desc_parts) if desc_parts else "No additional details."
            
            # Prepare request payload
            payload = {
                "key": TRELLO_API_KEY,
                "token": TRELLO_TOKEN,
                "idList": TRELLO_LIST_ID,
                "name": name,
                "desc": desc
            }
            
            logger.info("Creating Trello card", task_name=name, task_index=i)
            
            # Make API request
            response = requests.post(url, params=payload, timeout=30)
            response.raise_for_status()
            
            card_data = response.json()
            card_url = f"https://trello.com/c/{card_data['id']}"
            
            logger.info("Trello card created successfully", 
                       card_id=card_data['id'], 
                       card_name=name,
                       card_url=card_url)
            
            responses.append(TrelloCardResponse(
                id=card_data['id'],
                name=name,
                url=card_url,
                error=None
            ))
            
        except requests.exceptions.Timeout:
            logger.error("Trello API timeout", task_name=name, task_index=i)
            responses.append(TrelloCardResponse(
                id="",
                name=name,
                error="Request timeout"
            ))
            
        except requests.exceptions.HTTPError as e:
            logger.error("Trello API HTTP error", 
                        error=str(e), 
                        status_code=e.response.status_code if e.response else None,
                        task_name=name,
                        task_index=i)
            error_msg = f"HTTP {e.response.status_code}" if e.response else "HTTP Error"
            responses.append(TrelloCardResponse(
                id="",
                name=name,
                error=error_msg
            ))
            
        except requests.exceptions.RequestException as e:
            logger.error("Trello API request error", error=str(e), task_name=name, task_index=i)
            responses.append(TrelloCardResponse(
                id="",
                name=name,
                error="Request failed"
            ))
            
        except Exception as e:
            logger.error("Unexpected error creating Trello card", 
                        error=str(e), 
                        task_name=name, 
                        task_index=i)
            responses.append(TrelloCardResponse(
                id="",
                name=name,
                error="Unexpected error"
            ))
    
    successful_cards = sum(1 for r in responses if not r.error)
    logger.info("Trello card creation completed", 
               total=len(tasks), 
               successful=successful_cards, 
               failed=len(tasks) - successful_cards)
    
    return responses

def test_trello_connection() -> bool:
    """
    Test connection to Trello API.
    
    Returns:
        True if connection is successful, False otherwise
    """
    if not validate_trello_credentials():
        return False
    
    try:
        url = "https://api.trello.com/1/members/me"
        params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        logger.info("Trello connection test successful")
        return True
        
    except Exception as e:
        logger.error("Trello connection test failed", error=str(e))
        return False