
import json

from pydantic import ValidationError

from agents.quote_extraction.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from core.config import settings
from core.llm import get_llm_client
from schemas.quotation import Quotation


class QuoteExtractionError(Exception):
    """Raised when quotation extraction fails."""


def extract_quotation(document_text: str) -> Quotation:

    if not document_text.strip():
        raise ValueError("Quotation document text cannot be empty.")

    client = get_llm_client()

    # Step 1: Debug the input
    print("\n--- TEXT SENT TO GROQ ---")
    print(document_text[:500])

    # Step 2: Send the request to Groq
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_user_prompt(document_text),
            },
        ],
        temperature=0.1,
        max_completion_tokens=2000,
    )

    # Step 3: Read the response
    response_text = response.choices[0].message.content

    # Step 4: Debug the raw response
    print("\n--- RAW GROQ RESPONSE ---")
    print(response_text)

    if not response_text:
        raise QuoteExtractionError("The LLM returned an empty response.")

    # Step 5: Convert JSON into a dictionary
    try:
        extracted_data = json.loads(response_text)

    except json.JSONDecodeError as error:
        raise QuoteExtractionError(
            f"The LLM returned invalid JSON: {error}"
        ) from error

    # Step 6: Validate using Pydantic
    try:
        quotation = Quotation.model_validate(extracted_data)

    except ValidationError as error:
        raise QuoteExtractionError(
            f"Extracted quotation failed validation: {error}"
        ) from error

    return quotation
