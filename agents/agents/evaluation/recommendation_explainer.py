#This connects Groq to our evaluation results.


import json

from pydantic import ValidationError

from core.config import settings
from core.llm import get_llm_client

from agents.evaluation.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)


class RecommendationExplainer:

    def explain(self, evaluation_data: dict) -> dict:

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
                    "content": build_user_prompt(evaluation_data),
                },
            ],
            temperature=0.1,
            max_completion_tokens=1500,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content

        if not response_text:
            raise ValueError("Groq returned an empty response.")

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid recommendation JSON: {error}"
            ) from error

        required_fields = [
            "recommendation_summary",
            "recommendation_reasoning",
            "supplier_strengths",
            "supplier_weaknesses",
            "trade_offs",
        ]

        missing = [
            field for field in required_fields
            if field not in result
        ]

        if missing:
            raise ValueError(
                f"Recommendation response missing fields: {missing}"
            )

        return result
