"""
Gemini function declarations for all vault tools.

Defines each vault reader and writer function as a Gemini FunctionDeclaration
and wraps them in a Tool so they can be passed to generate_content. This is
the tool calling integration pattern — the LLM decides when to call each
function and the results are fed back into the conversation.

Usage::

    from src.tools.declarations import VAULT_TOOLS
    from google.genai.types import GenerateContentConfig

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=GenerateContentConfig(tools=[VAULT_TOOLS]),
    )
"""
from google.genai.types import FunctionDeclaration, Tool

from src.gemini_client import _client
from src.tools.categoriser import categorise_pantry
from src.tools.vault_reader import read_cocktail_log, read_pantry, read_preferences
from src.tools.vault_writer import write_suggestion, write_to_log

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

write_suggestion_declaration = FunctionDeclaration.from_callable(
    callable=write_suggestion,
    client=_client,
)

write_to_log_declaration = FunctionDeclaration.from_callable(
    callable=write_to_log,
    client=_client,
)

categorise_pantry_declaration = FunctionDeclaration.from_callable(
    callable=categorise_pantry,
    client=_client,
)

VAULT_TOOLS = Tool(
    function_declarations=[
        read_pantry_declaration,
        read_preferences_declaration,
        read_cocktail_log_declaration,
        write_suggestion_declaration,
        write_to_log_declaration,
        categorise_pantry_declaration,
    ]
)
