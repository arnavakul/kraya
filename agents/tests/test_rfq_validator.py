
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
        "email_body": """
        We request a quotation for Laptop.

        Quantity: 20
        Specifications: Intel i7, 16GB RAM, 512GB SSD
        Delivery location: Kolkata
        Mandatory requirement: 3-year warranty.
        """
    }

    result = validate_rfq_content(rfq_data, email_content)

    assert result["valid"] is True
    assert result["errors"] == []


def test_missing_mandatory_constraint():

    rfq_data = {
        "product_service": "Laptop",
        "quantity": 20,
        "specifications": "Intel i7, 16GB RAM, 512GB SSD",
        "delivery_location": "Kolkata",
        "mandatory_constraints": ["3-year warranty"]
    }

    email_content = {
        "email_subject": "RFQ - 20 Laptops",
        "email_body": """
        We request a quotation for Laptop.

        Quantity: 20
        Specifications: Intel i7, 16GB RAM, 512GB SSD
        Delivery location: Kolkata.
        """
    }

    result = validate_rfq_content(rfq_data, email_content)

    assert result["valid"] is False
    assert any(
        "3-year warranty" in error
        for error in result["errors"]
    )


def test_empty_email_is_rejected():

    result = validate_rfq_content(
        {"product_service": "Laptop"},
        {
            "email_subject": "",
            "email_body": ""
        }
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0
