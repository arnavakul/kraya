
import re
from urllib.parse import urlparse

from pydantic_models.email_message import EmailMessage
from pydantic_models.security_screening_result import (
    SecurityScreeningResult
)


PROMPT_INJECTION_PATTERNS = [
    r"ignore all previous instructions",
    r"disregard all previous instructions",
    r"ignore your system prompt",
    r"override (all )?(previous )?instructions",
    r"reveal (your )?(system prompt|hidden instructions)",
    r"act as (an? )?administrator",
]

SENSITIVE_DATA_PATTERNS = [
    r"reveal .*procurement budget",
    r"share .*confidential information",
    r"send .*internal pricing",
    r"provide .*password",
    r"reveal .*api key",
    r"share .*supplier database",
]

UNAUTHORIZED_ACTION_PATTERNS = [
    r"approve (our|this|the) quotation",
    r"approve (this|the) rfq",
    r"dispatch .*without approval",
    r"bypass .*approval",
    r"change .*bank details",
]

SUSPICIOUS_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".js",
    ".scr",
    ".msi",
}

URL_SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "rb.gy",
    "shorturl.at",
}


def _matches_patterns(text: str, patterns: list[str]) -> bool:

    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def _contains_suspicious_url(text: str) -> bool:

    urls = re.findall(r"https?://[^\s<>\"']+", text, re.IGNORECASE)

    for url in urls:

        url = url.rstrip(".,;!?)")

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                return True

            if parsed.username or parsed.password:
                return True

            if hostname.lower() in URL_SHORTENERS:
                return True

        except ValueError:
            return True

    return False


def _contains_unsafe_attachment(email: EmailMessage) -> bool:

    for attachment in email.attachments:

        filename = attachment.filename.lower()

        for extension in SUSPICIOUS_EXTENSIONS:
            if filename.endswith(extension):
                return True

    return False


def screen_email_security(
    email: EmailMessage
) -> SecurityScreeningResult:

    text = f"{email.subject}\n{email.body}"

    flags = []

    if _matches_patterns(text, PROMPT_INJECTION_PATTERNS):
        flags.append("prompt_injection")

    if _matches_patterns(text, SENSITIVE_DATA_PATTERNS):
        flags.append("sensitive_data_request")

    if _matches_patterns(text, UNAUTHORIZED_ACTION_PATTERNS):
        flags.append("unauthorized_action_request")

    if _contains_suspicious_url(text):
        flags.append("suspicious_url")

    if _contains_unsafe_attachment(email):
        flags.append("unsafe_attachment")

    high_risk_flags = {
        "prompt_injection",
        "sensitive_data_request",
        "unauthorized_action_request",
    }

    medium_risk_flags = {
        "suspicious_url",
        "unsafe_attachment",
    }

    if any(flag in high_risk_flags for flag in flags):
        risk_level = "high"

    elif any(flag in medium_risk_flags for flag in flags):
        risk_level = "medium"

    else:
        risk_level = "none"

    suspicious = len(flags) > 0

    return SecurityScreeningResult(
        email_id=email.email_id,
        risk_level=risk_level,
        is_suspicious=suspicious,
        requires_human_review=suspicious,
        security_flags=flags,
        screening_summary=(
            "Potential security risks detected."
            if suspicious
            else "No configured security patterns detected."
        )
    )

