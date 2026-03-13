import requests
from config import TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_LIST_ID

def create_trello_cards(tasks: list) -> list:
    """
    Create a Trello card for each task in the provided list.
    Returns list of responses.
    """
    if not TRELLO_API_KEY or not TRELLO_TOKEN or not TRELLO_LIST_ID:
        print("Trello credentials missing, skipping card creation.")
        return []

    url = "https://api.trello.com/1/cards"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "idList": TRELLO_LIST_ID,
    }
    responses = []

    for task in tasks:
        name = task.get("task", "Untitled task")
        desc_parts = []
        if task.get("assigned_to"):
            desc_parts.append(f"Assigned to: {task['assigned_to']}")
        if task.get("deadline"):
            desc_parts.append(f"Deadline: {task['deadline']}")
        desc = "\n".join(desc_parts) if desc_parts else "No additional details."

        payload = {**query, "name": name, "desc": desc}
        try:
            resp = requests.post(url, params=payload)
            resp.raise_for_status()
            responses.append(resp.json())
        except Exception as e:
            print(f"Failed to create Trello card: {e}")
            responses.append({"error": str(e)})

    return responses