
from schemas.policy import CheckStatus, PolicyCheckResult


class PermissionChecker:
    """
    Checks whether a user account and organization
    are eligible to perform a procurement action.

    Role-specific permissions will be configured separately.
    """

    def check_permission(
        self,
        user_role: str,
        user_status: str,
        organization_status: str,
        action: str,
    ) -> PolicyCheckResult:

        # Check whether the user account is active.
        if user_status.upper() != "ACTIVE":
            return PolicyCheckResult(
                check_name="user_status",
                status=CheckStatus.FAIL,
                reason="User account is not active.",
            )

        # Check whether the organization is active.
        if organization_status.upper() != "ACTIVE":
            return PolicyCheckResult(
                check_name="organization_status",
                status=CheckStatus.FAIL,
                reason="Organization is not active or verified.",
            )

        # Role-specific authorization is not assumed here.
        if not user_role.strip():
            return PolicyCheckResult(
                check_name="user_role",
                status=CheckStatus.UNKNOWN,
                reason="User role is missing.",
            )

        if not action.strip():
            return PolicyCheckResult(
                check_name="action",
                status=CheckStatus.UNKNOWN,
                reason="Requested action is missing.",
            )

        return PolicyCheckResult(
            check_name="account_eligibility",
            status=CheckStatus.PASS,
            reason=(
                "User and organization are active. "
                "Role-specific authorization must be checked "
                "against an approved permission policy."
            ),
        )
