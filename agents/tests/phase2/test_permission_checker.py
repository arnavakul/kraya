
from agents.policy_guardrails.permission_checker import PermissionChecker
from schemas.policy import CheckStatus


def test_active_user_and_organization_pass():
    checker = PermissionChecker()

    result = checker.check_permission(
        "ORG_ADMIN", "ACTIVE", "ACTIVE", "CREATE_RFQ"
    )

    assert result.status == CheckStatus.PASS


def test_inactive_user_fails():
    checker = PermissionChecker()

    result = checker.check_permission(
        "ORG_ADMIN", "INACTIVE", "ACTIVE", "CREATE_RFQ"
    )

    assert result.status == CheckStatus.FAIL
    assert "User account" in result.reason


def test_pending_organization_fails():
    checker = PermissionChecker()

    result = checker.check_permission(
        "ORG_ADMIN", "ACTIVE", "PENDING_VERIFICATION", "CREATE_RFQ"
    )

    assert result.status == CheckStatus.FAIL
    assert "Organization" in result.reason


def test_missing_role_returns_unknown():
    checker = PermissionChecker()

    result = checker.check_permission(
        "", "ACTIVE", "ACTIVE", "CREATE_RFQ"
    )

    assert result.status == CheckStatus.UNKNOWN
