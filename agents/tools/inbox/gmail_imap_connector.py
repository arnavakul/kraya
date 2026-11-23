import os
import imaplib
import email
from email.header import decode_header
import logging
from typing import Any
from datetime import datetime, timezone
from pydantic_models.email_message import EmailMessage

logger = logging.getLogger(__name__)

# In-memory store for autonomous mailbox messages (e.g. from webhooks, simulations, or direct replies)
AUTONOMOUS_INBOX_STORE: list[EmailMessage] = []

# Keep track of message IDs already ingested to prevent duplicate processing
PROCESSED_GMAIL_IDS: set[str] = set()


def add_to_autonomous_inbox(sender: str, subject: str, body: str, thread_id: str | None = None) -> EmailMessage:
    msg_id = f"EMAIL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"
    msg = EmailMessage(
        email_id=msg_id,
        sender_email=sender,
        sender_name=sender.split("@")[0] if "@" in sender else sender,
        subject=subject,
        body=body,
        thread_id=thread_id or "THREAD-DEFAULT"
    )
    AUTONOMOUS_INBOX_STORE.append(msg)
    return msg


def get_gmail_credentials() -> tuple[str | None, str | None]:
    user = os.getenv("GMAIL_USER") or os.getenv("IMAP_USER") or os.getenv("SMTP_USER")
    password = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("IMAP_PASSWORD") or os.getenv("SMTP_PASSWORD")
    if user:
        user = user.strip()
    if password:
        password = password.strip().replace(" ", "")  # Strip Google app password spaces
    return user, password


def update_gmail_credentials(user: str, app_password: str) -> None:
    """Updates in-memory credentials and appends/updates agents/.env"""
    cleaned_user = user.strip()
    cleaned_pass = app_password.strip().replace(" ", "")
    os.environ["GMAIL_USER"] = cleaned_user
    os.environ["GMAIL_APP_PASSWORD"] = cleaned_pass
    os.environ["SMTP_USER"] = cleaned_user
    os.environ["SMTP_PASSWORD"] = cleaned_pass

    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        updated_keys = set()
        new_lines = []
        for line in lines:
            if line.startswith("GMAIL_USER="):
                new_lines.append(f"GMAIL_USER={cleaned_user}\n")
                updated_keys.add("GMAIL_USER")
            elif line.startswith("GMAIL_APP_PASSWORD="):
                new_lines.append(f"GMAIL_APP_PASSWORD={cleaned_pass}\n")
                updated_keys.add("GMAIL_APP_PASSWORD")
            else:
                new_lines.append(line)
        
        if "GMAIL_USER" not in updated_keys:
            new_lines.append(f"GMAIL_USER={cleaned_user}\n")
        if "GMAIL_APP_PASSWORD" not in updated_keys:
            new_lines.append(f"GMAIL_APP_PASSWORD={cleaned_pass}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        logger.warning("Could not persist credentials to .env: %s", e)


def check_gmail_connection() -> dict[str, Any]:
    """Tests live connection to imap.gmail.com:993 and reports diagnostics."""
    user, password = get_gmail_credentials()
    if not user or not password:
        return {
            "configured": False,
            "connected": False,
            "account": None,
            "message": "Gmail credentials not configured. Please set your Gmail & App Password."
        }

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=10)
        mail.login(user, password)
        status, counts = mail.select("INBOX", readonly=True)
        inbox_count = int(counts[0].decode()) if status == "OK" and counts and counts[0] else 0
        mail.close()
        mail.logout()
        return {
            "configured": True,
            "connected": True,
            "account": user,
            "inbox_count": inbox_count,
            "message": f"Successfully connected to Gmail for {user} ({inbox_count} total messages in INBOX)."
        }
    except Exception as e:
        logger.warning("Gmail connection test failed: %s", e)
        return {
            "configured": True,
            "connected": False,
            "account": user,
            "error": str(e),
            "message": f"Failed to connect to Gmail: {str(e)}"
        }


def decode_str_header(header_val: str | None) -> str:
    if not header_val:
        return ""
    try:
        decoded_list = decode_header(header_val)
        parts = []
        for text, enc in decoded_list:
            if isinstance(text, bytes):
                parts.append(text.decode(enc or "utf-8", errors="ignore"))
            else:
                parts.append(str(text))
        return " ".join(parts).strip()
    except Exception:
        return str(header_val)


def fetch_emails_from_gmail(supplier_filter: str | None = None) -> list[EmailMessage]:
    user, password = get_gmail_credentials()
    fetched_messages: list[EmailMessage] = []

    # 1. Live Gmail IMAP check if credentials exist
    if user and password:
        try:
            logger.info("Connecting to Gmail IMAP (imap.gmail.com) for user: %s", user)
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=12)
            mail.login(user, password)
            mail.select("INBOX")

            # Search ALL recent messages (not only UNSEEN, because user might have read it in browser)
            status, messages = mail.search(None, "ALL")
            if status == "OK" and messages[0]:
                all_nums = messages[0].split()
                # Inspect the most recent 25 messages in INBOX (newest first)
                recent_nums = list(reversed(all_nums[-25:]))

                for num in recent_nums:
                    msg_id_str = num.decode()
                    if msg_id_str in PROCESSED_GMAIL_IDS:
                        continue

                    res, data = mail.fetch(num, "(RFC822)")
                    if res != "OK" or not data or not data[0]:
                        continue

                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject_text = decode_str_header(msg.get("Subject", ""))
                    sender_header = decode_str_header(msg.get("From", ""))
                    to_header = decode_str_header(msg.get("To", ""))
                    message_id_header = msg.get("Message-ID", f"GMAIL-{msg_id_str}")

                    # Extract body text
                    body_text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body_text = payload.decode(errors="ignore")
                                    break
                            elif content_type == "text/html" and not body_text:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    # Very basic strip of HTML tags
                                    import re
                                    body_text = re.sub(r'<[^>]+>', ' ', payload.decode(errors="ignore"))
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body_text = payload.decode(errors="ignore")

                    body_clean = body_text.strip()
                    if not body_clean:
                        continue

                    # Filter evaluation:
                    # Check if from supplier, or subject mentions RFQ / Quotation / Kraya / Quote
                    is_match = False
                    sender_lower = sender_header.lower()
                    subj_lower = subject_text.lower()

                    # Don't match our own sent messages
                    if user.lower() in sender_lower and not (supplier_filter and user.lower() in supplier_filter.lower()):
                        continue

                    if supplier_filter and "@" in supplier_filter:
                        filter_clean = supplier_filter.strip().lower()
                        if filter_clean in sender_lower or sender_lower in filter_clean:
                            is_match = True
                        elif "rfq" in subj_lower or "quotation" in subj_lower or "kraya" in subj_lower:
                            is_match = True
                    else:
                        # Match any supplier quotation or RFQ reply
                        if any(kw in subj_lower for kw in ["rfq", "quotation", "quote", "kraya", "pricing", "proposal"]):
                            is_match = True
                        elif any(kw in body_clean.lower() for kw in ["unit price", "total price", "quotation", "warranty", "net 30"]):
                            is_match = True

                    if is_match:
                        PROCESSED_GMAIL_IDS.add(msg_id_str)
                        email_msg = EmailMessage(
                            email_id=f"GMAIL-{msg_id_str}",
                            sender_email=sender_header,
                            sender_name=sender_header.split("<")[0].replace('"', '').strip() if "<" in sender_header else sender_header,
                            subject=subject_text,
                            body=body_clean,
                            thread_id=message_id_header
                        )
                        fetched_messages.append(email_msg)
                        logger.info("Found relevant supplier reply from %s: '%s'", sender_header, subject_text)

            mail.close()
            mail.logout()
            logger.info("Polled Gmail IMAP inbox: %d matching supplier replies found", len(fetched_messages))
        except Exception as e:
            logger.warning("Live Gmail IMAP poll failed: %s", e)

    # 2. Also drain any messages queued in the autonomous store (simulations/direct pastes)
    while AUTONOMOUS_INBOX_STORE:
        fetched_messages.append(AUTONOMOUS_INBOX_STORE.pop(0))

    return fetched_messages
