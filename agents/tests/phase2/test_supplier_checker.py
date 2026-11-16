
from agents.policy_guardrails.supplier_checker import SupplierChecker
from schemas.policy import CheckStatus


def test_active_supplier_passes():
    result = SupplierChecker().check_supplier("ACTIVE")
    assert result.status == CheckStatus.PASS


def test_inactive_supplier_fails():
    result = SupplierChecker().check_supplier("INACTIVE")
    assert result.status == CheckStatus.FAIL


def test_blocked_supplier_fails():
    result = SupplierChecker().check_supplier("BLOCKED")
    assert result.status == CheckStatus.FAIL


def test_missing_supplier_status_is_unknown():
    result = SupplierChecker().check_supplier(None)
    assert result.status == CheckStatus.UNKNOWN


def test_unknown_supplier_status():
    result = SupplierChecker().check_supplier("PENDING")
    assert result.status == CheckStatus.UNKNOWN
