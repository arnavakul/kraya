
def validate_rfq_content(
    rfq_data: dict,
    email_content: dict
) -> dict:

    errors = []

    email_body = email_content.get(
        "email_body", ""
    ).casefold()

    email_subject = email_content.get(
        "email_subject", ""
    ).strip()

    if not email_subject:
        errors.append("Email subject is missing.")

    if not email_body.strip():
        errors.append("Email body is empty.")

    mandatory_fields = [
        "product_service",
        "quantity",
        "specifications",
        "delivery_location"
    ]

    for field in mandatory_fields:

        value = rfq_data.get(field)

        if value is None or value == "":
            continue

        # Normalize integer-valued numeric fields
        if isinstance(value, (int, float)) and value.is_integer() if isinstance(value, float) else False:
            expected_value = str(int(value))
        else:
            expected_value = str(value)

        if expected_value.casefold() not in email_body:
            errors.append(
                f"RFQ email does not explicitly contain {field}: {value}"
            )

    for constraint in rfq_data.get(
        "mandatory_constraints", []
    ):

        if constraint.casefold() not in email_body:
            errors.append(
                f"Mandatory constraint missing: {constraint}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
