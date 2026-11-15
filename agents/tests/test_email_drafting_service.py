
from unittest.mock import patch

from tools.rfq.email_drafting_service import (
    draft_rfq_email,
    RFQEmailContent
)


@patch("tools.rfq.email_drafting_service.get_llm")
def test_draft_rfq_email(mock_get_llm):

    mock_structured_llm = mock_get_llm.return_value.with_structured_output.return_value

    mock_structured_llm.invoke.return_value = RFQEmailContent(
        email_subject="RFQ - 20 Laptops",
        email_body="Please provide your quotation for 20 laptops."
    )

    result = draft_rfq_email({
        "supplier_name": "Test Supplier",
        "product_service": "Laptop",
        "quantity": 20
    })

    assert result["email_subject"] == "RFQ - 20 Laptops"
    assert "20 laptops" in result["email_body"]

    mock_get_llm.assert_called_once_with(temperature=0)


@patch("tools.rfq.email_drafting_service.get_llm")
def test_reject_empty_email_body(mock_get_llm):

    mock_structured_llm = mock_get_llm.return_value.with_structured_output.return_value

    mock_structured_llm.invoke.return_value = RFQEmailContent(
        email_subject="RFQ - Laptops",
        email_body="   "
    )

    try:
        draft_rfq_email({"product_service": "Laptop"})
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "body is empty" in str(error)

