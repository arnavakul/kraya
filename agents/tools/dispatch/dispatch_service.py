
from tools.dispatch.dispatch_models import EmailMessage
from tools.dispatch.dispatch_repository import (
    DispatchRepository,
    DuplicateDispatchError,
    DispatchStateError
)
from tools.dispatch.idempotency import generate_idempotency_key


class AmbiguousEmailSendError(Exception):
    """The provider outcome cannot be determined."""


class DispatchService:

    def __init__(self, provider, repository=None):
        self.provider = provider
        self.repository = repository or DispatchRepository()

    def dispatch_rfq(self, rfq: dict) -> dict:

        # 1. Enforce human approval
        if rfq.get("status") != "approved":
            raise ValueError(
                "Only approved RFQs can be dispatched."
            )

        # 2. Validate supplier recipient
        supplier = rfq.get("supplier", {})
        recipient_email = supplier.get("contact_email")

        if not recipient_email:
            raise ValueError("Supplier recipient email is missing.")

        # 3. Validate RFQ details and construct the message
        rfq_id = rfq.get("rfq_id")
        subject = rfq.get("email_subject")
        body = rfq.get("email_body")

        if not rfq_id:
            raise ValueError("RFQ ID is missing.")

        if not subject or not subject.strip():
            raise ValueError("RFQ email subject is missing.")

        if not body or not body.strip():
            raise ValueError("RFQ email body is missing.")

        idempotency_key = generate_idempotency_key(
            str(rfq_id),
            recipient_email
        )

        message = EmailMessage(
            rfq_id=rfq_id,
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            idempotency_key=idempotency_key
        )

        # 4. Register dispatch
        try:
            record = self.repository.create_dispatch({
                "rfq_id": str(rfq_id),
                "recipient_email": message.recipient_email,
                "subject": subject,
                "idempotency_key": idempotency_key
            })

        except DuplicateDispatchError:
            existing = self.repository.get_by_idempotency_key(
                idempotency_key
            )

            return {
                "status": "duplicate",
                "dispatch_id": (
                    str(existing["dispatch_id"])
                    if existing else None
                ),
                "existing_status": (
                    existing["status"]
                    if existing else "unknown"
                ),
                "message": "Dispatch already exists. No email was sent."
            }

        dispatch_id = str(record["dispatch_id"])

        # 5. Atomically claim dispatch
        try:
            self.repository.claim_dispatch(dispatch_id)

        except DispatchStateError:
            return {
                "status": "not_claimed",
                "dispatch_id": dispatch_id,
                "message": "Dispatch could not be claimed."
            }

        # 6. Send through provider
        try:
            result = self.provider.send(message)

        except Exception as error:
            # An exception does not prove the provider rejected the email.
            # Treat the outcome as uncertain to avoid duplicate delivery.
            try:
                self.repository.update_status(
                    dispatch_id=dispatch_id,
                    status="unknown",
                    last_error=str(error)
                )
            except Exception:
                # The database may be unavailable as well.
                # The record may remain in 'sending' and needs reconciliation.
                pass

            return {
                "status": "unknown",
                "dispatch_id": dispatch_id,
                "error": str(error),
                "message": (
                    "Email outcome is uncertain. "
                    "Do not automatically retry."
                )
            }

        # 7. Record provider result
        if result.success:
            self.repository.update_status(
                dispatch_id=dispatch_id,
                status="sent",
                provider=result.provider,
                provider_message_id=result.provider_message_id
            )

            return {
                "status": "sent",
                "dispatch_id": dispatch_id,
                "provider_message_id": result.provider_message_id
            }

        # A provider-reported failure is treated as definitive.
        # Real adapters must only report this when rejection is confirmed.
        self.repository.update_status(
            dispatch_id=dispatch_id,
            status="failed",
            provider=result.provider,
            last_error=result.error
        )

        return {
            "status": "failed",
            "dispatch_id": dispatch_id,
            "error": result.error
        }
