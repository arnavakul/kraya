
def assemble_rfq_email(
    rfq_data: dict,
    email_content: dict
) -> dict:

    specifications = rfq_data.get("specifications")
    quality = rfq_data.get("quality_requirements")
    constraints = rfq_data.get("mandatory_constraints", [])
    preferences = rfq_data.get("preferences", [])

    lines = [
        email_content["opening_message"],
        "",
        "REQUEST FOR QUOTATION",
        "",
        f"Product/Service: {rfq_data['product_service']}",
        f"Quantity: {rfq_data['quantity']}",
    ]

    if specifications:
        lines.append(f"Specifications: {specifications}")

    if quality:
        lines.append(f"Quality Requirements: {quality}")

    lines.extend([
        f"Delivery Location: {rfq_data['delivery_location']}"
    ])

    if rfq_data.get("delivery_deadline"):
        lines.append(
            f"Delivery Deadline: {rfq_data['delivery_deadline']}"
        )

    if rfq_data.get("budget") is not None:
        lines.append(
            f"Budget: {rfq_data['currency']} {rfq_data['budget']}"
        )

    if constraints:
        lines.extend(["", "Mandatory Requirements:"])

        for constraint in constraints:
            lines.append(f"- {constraint}")

    if preferences:
        lines.extend(["", "Preferences:"])

        for preference in preferences:
            lines.append(f"- {preference}")

    lines.extend([
        "",
        "Please include the following in your quotation:",
        "- Unit price",
        "- Total price",
        "- Applicable taxes",
        "- Delivery timeline",
        "- Warranty details",
        "- Payment terms",
        "- Quotation validity",
        "",
        email_content["closing_message"]
    ])

    return {
        "email_subject": email_content["email_subject"],
        "email_body": "\n".join(lines)
    }
