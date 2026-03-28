"""
Gemini API client for Cocktail Cabinet.

Initialises the google-genai SDK and exposes a simple interface for
sending prompts to the Gemini model.
"""
from google import genai

from src.config import GEMINI_API_KEY

_client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"


def generate(prompt: str) -> str:
    """Send a prompt to Gemini and return the response text.

    Args:
        prompt: The text prompt to send to the model.

    Returns:
        The model's response as a plain string.
    """
    response = _client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return response.text
