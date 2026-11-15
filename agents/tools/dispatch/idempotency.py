
import hashlib


def generate_idempotency_key(
    rfq_id: str,
    recipient_email: str
) -> str:

    normalized_email = recipient_email.strip().lower()

    raw_key = f"{rfq_id}:{normalized_email}"

    return hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()
