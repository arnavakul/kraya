from pydantic_models.email_message import EmailMessage
from pydantic_models.inbox_triage_result import (
    QuotationProcessingResult,
    SupplierIntentProcessingResult,
)
from schemas.suppliers_intent import (
    RecommendedAction,
    SupplierIntent,
)


ATTACHMENT_CONTENT_WARNING = (
    "Attachment content is unavailable through the current email message "
    "contract; only the email body was analyzed."
)


def process_quotation_message(
    email: EmailMessage,
    quote_agent=None,
) -> QuotationProcessingResult:
    """Run Agent 6 on the text the current inbox contract actually carries."""

    if quote_agent is None:
        from agents.quote_extraction.agent import QuoteExtractionAgent

        quote_agent = QuoteExtractionAgent()

    try:
        result = quote_agent.process_text(email.body)
        quotation = result["quotation"]
        validation_report = result["validation_report"]

        validation = {
            "status": validation_report.status.value,
            "errors": list(validation_report.errors),
            "warnings": list(validation_report.warnings),
        }

        if email.attachments:
            validation["warnings"].append(ATTACHMENT_CONTENT_WARNING)
            if validation["status"] == "VALID":
                validation["status"] = "WARNING"

        review_required = (
            validation["status"] != "VALID"
            or bool(email.attachments)
        )

        return QuotationProcessingResult(
            email_id=email.email_id,
            thread_id=email.thread_id,
            in_reply_to=email.in_reply_to,
            sender_email=email.sender_email,
            sender_name=email.sender_name,
            status="needs_review" if review_required else "completed",
            quotation=quotation.model_dump(mode="json"),
            financial_validation=validation,
            requires_human_review=review_required,
        )

    except Exception as error:
        return QuotationProcessingResult(
            email_id=email.email_id,
            thread_id=email.thread_id,
            in_reply_to=email.in_reply_to,
            sender_email=email.sender_email,
            sender_name=email.sender_name,
            status="failed",
            error=str(error)[:2000],
            requires_human_review=True,
        )


def process_clarification_message(
    email: EmailMessage,
    intent_agent=None,
) -> SupplierIntentProcessingResult:
    """Run Agent 7 using the body and subject available in the inbox item."""

    if intent_agent is None:
        from agents.supplier_intent.agent import SupplierIntentAgent

        intent_agent = SupplierIntentAgent()

    try:
        analysis = intent_agent.process_message(
            supplier_message=email.body,
            rfq_context=email.subject,
            # The current message contract has thread IDs, not prior messages.
            conversation_history="",
        )

        review_required = (
            analysis.requires_human_review
            or analysis.intent == SupplierIntent.UNCLEAR
            or analysis.recommended_action
            == RecommendedAction.ESCALATE_TO_HUMAN
        )

        if review_required and not analysis.requires_human_review:
            analysis = analysis.model_copy(
                update={"requires_human_review": True}
            )

        return SupplierIntentProcessingResult(
            email_id=email.email_id,
            thread_id=email.thread_id,
            in_reply_to=email.in_reply_to,
            sender_email=email.sender_email,
            sender_name=email.sender_name,
            status="completed",
            analysis=analysis,
            requires_human_review=review_required,
        )

    except Exception as error:
        return SupplierIntentProcessingResult(
            email_id=email.email_id,
            thread_id=email.thread_id,
            in_reply_to=email.in_reply_to,
            sender_email=email.sender_email,
            sender_name=email.sender_name,
            status="failed",
            error=str(error)[:2000],
            requires_human_review=True,
        )
