
from decimal import Decimal, InvalidOperation

from schemas.policy import CheckStatus, PolicyCheckResult


class SpendingChecker:
    """Checks procurement amounts against approved spending limits."""

    def check_spending(
        self,
        amount,
        spending_limit,
        currency: str | None,
        spending_limit_currency: str | None,
    ) -> PolicyCheckResult:

        # Required information must be available.
        if amount is None or spending_limit is None:
            return PolicyCheckResult(
                check_name="spending_limit",
                status=CheckStatus.UNKNOWN,
                reason="Amount or spending limit is missing.",
            )

        if not currency or not spending_limit_currency:
            return PolicyCheckResult(
                check_name="spending_currency",
                status=CheckStatus.UNKNOWN,
                reason="Currency information is missing.",
            )

        # Never compare amounts in different currencies.
        if currency.strip().upper() != spending_limit_currency.strip().upper():
            return PolicyCheckResult(
                check_name="spending_currency",
                status=CheckStatus.UNKNOWN,
                reason="Amount and spending limit use different currencies.",
            )

        try:
            amount = Decimal(str(amount))
            spending_limit = Decimal(str(spending_limit))
        except (InvalidOperation, ValueError):
            return PolicyCheckResult(
                check_name="spending_limit",
                status=CheckStatus.UNKNOWN,
                reason="Amount or spending limit is invalid.",
            )

        if not amount.is_finite() or not spending_limit.is_finite():
            return PolicyCheckResult(
                check_name="spending_limit",
                status=CheckStatus.UNKNOWN,
                reason="Amount or spending limit is not a finite number.",
            )

        if amount < 0 or spending_limit < 0:
            return PolicyCheckResult(
                check_name="spending_limit",
                status=CheckStatus.FAIL,
                reason="Negative amounts or spending limits are not allowed.",
            )

        # Compare the procurement amount with the approved limit.
        if amount > spending_limit:
            return PolicyCheckResult(
                check_name="spending_limit",
                status=CheckStatus.FAIL,
                reason=(
                    f"Procurement amount {amount} {currency.upper()} "
                    f"exceeds the spending limit of "
                    f"{spending_limit} {currency.upper()}."
                ),
            )

        return PolicyCheckResult(
            check_name="spending_limit",
            status=CheckStatus.PASS,
            reason=(
                f"Procurement amount is within the approved spending "
                f"limit of {spending_limit} {currency.upper()}."
            ),
        )
