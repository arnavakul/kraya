
import pytest

from tools.intake.requirement_parser import (
    parse_requirement
)

from langchain_google_genai.chat_models import GoogleAPIError


def test_gemini_requirement_extraction():

    try:

        result = parse_requirement(
            """
            I need 20 laptops with Intel i7,
            16GB RAM and 512GB SSD.

            Budget is 20 lakh INR.
            Delivery location is Kolkata.
            Delivery deadline is 15 December 2026.
            A 3-year warranty is mandatory.
            """
        )

    except GoogleAPIError as error:

        if error.code == 503:
            pytest.skip(
                "Gemini temporarily unavailable (503)"
            )

        raise

    assert result.product_service is not None

    assert result.quantity == 20

    assert result.delivery_location is not None

    assert result.budget == 2000000

    assert result.currency == "INR"

    print(result.model_dump(mode="json"))
