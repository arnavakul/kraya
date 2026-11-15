
from tools.rfq.rfq_assembler import assemble_rfq_email


def validate_rfq_content(
    rfq_data: dict,
    email_content: dict
) -> dict:

    errors = []

    required_fields = [
        "product_service",
        "quantity",
        "delivery_location"
    ]

    for field in required_fields:

        if rfq_data.get(field) is None:
            errors.append(f"Missing required RFQ field: {field}")

    if not email_content.get("email_subject", "").strip():
        errors.append("Email subject is missing.")

    if not email_content.get("opening_message", "").strip():
        errors.append("Opening message is missing.")

    if not email_content.get("closing_message", "").strip():
        errors.append("Closing message is missing.")

    if errors:
        return {"valid": False, "errors": errors}

    # Rebuild the expected email deterministically.
    expected = assemble_rfq_email(
        rfq_data,
        email_content
    )

    if not expected["email_body"].strip():
        errors.append("Final RFQ email body is empty.")

    if expected["email_subject"] != email_content["email_subject"]:
        errors.append("Email subject mismatch.")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
