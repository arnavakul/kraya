
import json

from pydantic import ValidationError

from core.config import settings
from core.llm import get_llm_client

from agents.supplier_intent.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)

from schemas.suppliers_intent import SupplierIntentAnalysis


class SupplierIntentError(Exception):
    """Raised when supplier intent analysis fails."""


def normalize_response(data: dict) -> dict:
    """Normalize alternative LLM field names to our schema."""

    aliases = {
        "intent": ["supplier_intent"],
        "intent_summary": ["summary", "reasoning"],
        "mentioned_details": ["provided_information", "details"],
        "missing_information": ["missing_fields"],
        "supplier_questions": ["questions_asked"],
        "recommended_action": ["next_action", "action"],
        "clarification_questions": ["questions_to_ask"],
        "draft_reply": ["suggested_reply", "response"],
        "requires_human_review": ["human_review_required"],
    }

    for standard_name, alternative_names in aliases.items():
        if standard_name not in data:
            for alternative in alternative_names:
                if alternative in data:
                    data[standard_name] = data[alternative]
                    break

    data.setdefault("intent", "unclear")
    data.setdefault("intent_summary", "Supplier message analyzed.")
    data.setdefault("mentioned_details", [])
    data.setdefault("missing_information", [])
    data.setdefault("supplier_questions", [])
    data.setdefault("recommended_action", "no_action")
    data.setdefault("clarification_questions", [])
    data.setdefault("draft_reply", None)
    data.setdefault("requires_human_review", False)

    return data


def analyze_supplier_message(
    supplier_message: str,
    rfq_context: str = "",
    conversation_history: str = "",
) -> SupplierIntentAnalysis:

    if not supplier_message.strip():
        raise ValueError("Supplier message cannot be empty.")

    client = get_llm_client()

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_user_prompt(
                    supplier_message,
                    rfq_context,
                    conversation_history,
                ),
            },
        ],
        temperature=0.1,
        max_completion_tokens=1500,
        response_format={"type": "json_object"},
    )

    response_text = response.choices[0].message.content

    if not response_text:
        raise SupplierIntentError(
            "The LLM returned an empty response."
        )

    # Remove Markdown code fences if the model includes them.
    cleaned_response = response_text.strip()

    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response.strip("`")
        if cleaned_response.startswith("json"):
            cleaned_response = cleaned_response[4:].strip()

    try:
        extracted_data = json.loads(cleaned_response)

    except json.JSONDecodeError as error:
        raise SupplierIntentError(
            f"The LLM returned invalid JSON: {error}"
        ) from error

    extracted_data = normalize_response(extracted_data)

    try:
        analysis = SupplierIntentAnalysis.model_validate(
            extracted_data
        )

    except ValidationError as error:
        raise SupplierIntentError(
            f"Supplier intent validation failed: {error}"
        ) from error

    return analysis

