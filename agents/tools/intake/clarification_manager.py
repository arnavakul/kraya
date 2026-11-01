
FIELD_QUESTIONS = {

    "product_service":
        "What product or service do you need?",

    "quantity":
        "What quantity do you require?",

    "delivery_location":
        "Where should the product or service be delivered?",

    "budget":
        "What is your estimated procurement budget?",

    "delivery_deadline":
        "When do you need the delivery?",

    "currency":
        "Which currency should be used for the budget?",

    "specifications":
        "Could you provide the technical specifications?"
}


def generate_clarification_questions(
    missing_fields: list[str],
    errors: list[str] | None = None
):

    questions = []

    for field in missing_fields:

        question = FIELD_QUESTIONS.get(field)

        if question:
            questions.append(question)

    for error in errors or []:

        questions.append(
            f"Please correct the following issue: {error}"
        )

    return questions
