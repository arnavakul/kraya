
from schemas.policy import CheckStatus, PolicyCheckResult


class SupplierChecker:
    """Checks whether a supplier is eligible for procurement."""

    def check_supplier(self, supplier_status: str | None) -> PolicyCheckResult:

        if not supplier_status or not supplier_status.strip():
            return PolicyCheckResult(
                check_name="supplier_status",
                status=CheckStatus.UNKNOWN,
                reason="Supplier status is missing.",
            )

        status = supplier_status.strip().upper()

        if status == "ACTIVE":
            return PolicyCheckResult(
                check_name="supplier_status",
                status=CheckStatus.PASS,
                reason="Supplier is active and eligible for procurement.",
            )

        if status in {"INACTIVE", "BLOCKED"}:
            return PolicyCheckResult(
                check_name="supplier_status",
                status=CheckStatus.FAIL,
                reason=f"Supplier is {status.lower()} and cannot be used.",
            )

        return PolicyCheckResult(
            check_name="supplier_status",
            status=CheckStatus.UNKNOWN,
            reason=f"Unrecognized supplier status: {status}.",
        )
