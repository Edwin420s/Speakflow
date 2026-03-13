import openai
import json
import re

from config import OPENAI_API_KEY, OPENAI_MODEL

openai.api_key = OPENAI_API_KEY

def load_prompt_template() -> str:
    """Read the prompt template from file."""
    with open("prompts/task_extraction.txt", "r") as f:
        return f.read()

def extract_tasks_and_summary(transcript: str) -> dict:
    """
    Call OpenAI to extract tasks and summary from the transcript.
    Returns a dict with keys 'tasks' (list) and 'summary' (str).
    """
    template = load_prompt_template()
    prompt = template.replace("{transcript}", transcript)

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=800
    )

    content = response["choices"][0]["message"]["content"]

    # Try to extract JSON from the response (the model may wrap it in markdown)
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        content = json_match.group()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: return empty structure
        result = {"tasks": [], "summary": "Could not parse response."}

    return result