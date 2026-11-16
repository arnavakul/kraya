
import json
from decimal import Decimal

from pydantic import ValidationError

from core.config import settings
from core.llm import get_llm_client

from agents.negotiations.prompts import (
    SYSTEM_PROMPT,
    build_negotiation_prompt,
)

from schemas.negotiation import (
    NegotiationContext,
    NegotiationPolicy,
    CounterOffer,
)


class NegotiatorError(Exception):
    """Raised when negotiation proposal generation fails."""


class Negotiator:
    """Generates structured supplier counteroffers using Groq."""

    def __init__(self):
        self.client = get_llm_client()

    def generate_counteroffer(
        self,
        context: NegotiationContext,
        policy: NegotiationPolicy,
    ) -> CounterOffer:

        if context.current_price is None:
            raise ValueError(
                "Current supplier price is required for negotiation."
            )

        if policy.minimum_acceptable_price is None:
            raise ValueError(
                "Minimum acceptable price must be configured."
            )

        prompt = build_negotiation_prompt(
            context=context.model_dump(mode="json"),
            policy=policy.model_dump(mode="json"),
        )

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_completion_tokens=1200,
                response_format={"type": "json_object"},
            )

            response_text = response.choices[0].message.content

            if not response_text:
                raise NegotiatorError(
                    "Groq returned an empty response."
                )

            data = json.loads(response_text)

            # Convert numeric values into Decimal for financial precision.
            if data.get("proposed_price") is not None:
                data["proposed_price"] = Decimal(
                    str(data["proposed_price"])
                )

            return CounterOffer.model_validate(data)

        except json.JSONDecodeError as error:
            raise NegotiatorError(
                "Groq returned invalid JSON."
            ) from error

        except ValidationError as error:
            raise NegotiatorError(
                f"Counteroffer validation failed: {error}"
            ) from error

        except Exception as error:
            if isinstance(error, NegotiatorError):
                raise
            raise NegotiatorError(
                f"Counteroffer generation failed: {error}"
            ) from error
