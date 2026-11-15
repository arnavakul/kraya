
from tools.rfq.rfq_assembler import assemble_rfq_email


def test_assembler_preserves_approved_requirements():

    rfq_data = {
        "product_service": "Laptop",
        "quantity": 20.0,
        "specifications": "Intel i7, 16GB RAM, 512GB SSD",
        "delivery_location": "Kolkata",
        "delivery_deadline": "2026-12-15",
        "budget": 2000000,
        "currency": "INR",
        "mandatory_constraints": ["3-year warranty"],
        "preferences": []
    }

    email_content = {
        "email_subject": "RFQ - Laptops",
        "opening_message": "Dear Supplier, please review our requirement.",
        "closing_message": "We look forward to your quotation."
    }

    result = assemble_rfq_email(rfq_data, email_content)

    body = result["email_body"]

    assert "Quantity: 20.0" in body
    assert "Intel i7, 16GB RAM, 512GB SSD" in body
    assert "Delivery Location: Kolkata" in body
    assert "3-year warranty" in body
    assert "INR 2000000" in body
