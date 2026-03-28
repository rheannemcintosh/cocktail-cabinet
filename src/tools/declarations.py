"""
Gemini function declarations for the vault reader tools.

Defines each vault reader function as a Gemini FunctionDeclaration and
wraps them in a Tool so they can be passed to generate_content. This is
the tool calling integration pattern — the LLM decides when to call each
function and the results are fed back into the conversation.

Usage::

    from src.tools.declarations import VAULT_READER_TOOL
    from google.genai.types import GenerateContentConfig

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=GenerateContentConfig(tools=[VAULT_READER_TOOL]),
    )
"""
from google.genai.types import FunctionDeclaration, Tool

from src.tools.vault_reader import read_cocktail_log, read_pantry, read_preferences
from src.gemini_client import _client

read_pantry_declaration = FunctionDeclaration.from_callable(
    callable=read_pantry,
    client=_client,
)

read_preferences_declaration = FunctionDeclaration.from_callable(
    callable=read_preferences,
    client=_client,
)

read_cocktail_log_declaration = FunctionDeclaration.from_callable(
    callable=read_cocktail_log,
    client=_client,
)

VAULT_READER_TOOL = Tool(
    function_declarations=[
        read_pantry_declaration,
        read_preferences_declaration,
        read_cocktail_log_declaration,
    ]
)
