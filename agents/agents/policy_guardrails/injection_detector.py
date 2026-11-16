
import re

from schemas.policy import CheckStatus, PolicyCheckResult


class InjectionDetector:
    """Detects common prompt-injection patterns in untrusted messages."""

    PATTERNS = {
        "instruction_override": (
            r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
            r"override\s+(the\s+)?(system|developer|previous)\s+instructions",
        ),
        "approval_bypass": (
            r"bypass\s+(the\s+)?(approval|security|policy|guardrails)",
            r"skip\s+(the\s+)?(approval|verification|security)\s+(process|check)",
        ),
        "confidential_data_request": (
            r"(reveal|disclose|share|expose)\s+.{0,40}"
            r"(confidential|secret|private)\s+(data|information|details)",
            r"(reveal|disclose|share|expose)\s+.{0,40}"
            r"(api\s*key|password|credentials)",
        ),
        "privilege_escalation": (
            r"you\s+are\s+now\s+(the\s+)?"
            r"(system\s+administrator|admin|system)",
        ),
    }

    def check_message(self, message: str | None) -> PolicyCheckResult:
        if not message or not message.strip():
            return PolicyCheckResult(
                check_name="prompt_injection",
                status=CheckStatus.UNKNOWN,
                reason="Message is empty or missing.",
            )

        detected_categories = []

        for category, patterns in self.PATTERNS.items():
            if any(
                re.search(pattern, message, re.IGNORECASE)
                for pattern in patterns
            ):
                detected_categories.append(category)

        if detected_categories:
            return PolicyCheckResult(
                check_name="prompt_injection",
                status=CheckStatus.FAIL,
                reason=(
                    "Suspicious instruction patterns detected: "
                    + ", ".join(detected_categories)
                ),
            )

        return PolicyCheckResult(
            check_name="prompt_injection",
            status=CheckStatus.PASS,
            reason="No known prompt-injection patterns detected.",
        )
