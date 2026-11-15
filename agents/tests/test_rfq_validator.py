
from tools.rfq.rfq_validator import validate_rfq_content


def test_valid_rfq_content():

    rfq_data = {
        "product_service": "Laptop",
        "quantity": 20,
        "specifications": "Intel i7, 16GB RAM, 512GB SSD",
        "delivery_location": "Kolkata",
        "mandatory_constraints": ["3-year warranty"]
    }

    email_content = {
        "email_subject": "RFQ - 20 Laptops",
        "opening_message": "Dear Supplier, please review our requirement.",
        "closing_message": "We look forward to your quotation."
    }

    result = validate_rfq_content(rfq_data, email_content)

    assert result["valid"] is True
    assert result["errors"] == []


def test_missing_mandatory_constraint():

    rfq_data = {
        "product_service": "Laptop",
        "quantity": 20,
        "delivery_location": "Kolkata",
        "mandatory_constraints": ["3-year warranty"]
    }

    email_content = {
        "email_subject": "RFQ - Laptops",
        "opening_message": "Dear Supplier.",
        "closing_message": "Please send your quotation."
    }

    result = validate_rfq_content(rfq_data, email_content)

    # The constraint is assembled from canonical data,
    # not expected in Gemini's generated message.
    assert result["valid"] is True


def test_empty_email_is_rejected():

    result = validate_rfq_content(
        {"product_service": "Laptop"},
        {
            "email_subject": "",
            "opening_message": "",
            "closing_message": ""
        }
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0
