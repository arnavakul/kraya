
from agents.policy_guardrails.spending_checker import SpendingChecker
from schemas.policy import CheckStatus


def test_amount_within_limit():
    checker = SpendingChecker()

    result = checker.check_spending(50000, 100000, "INR", "INR")

    assert result.status == CheckStatus.PASS


def test_amount_exceeds_limit():
    checker = SpendingChecker()

    result = checker.check_spending(150000, 100000, "INR", "INR")

    assert result.status == CheckStatus.FAIL


def test_missing_spending_limit():
    checker = SpendingChecker()

    result = checker.check_spending(50000, None, "INR", "INR")

    assert result.status == CheckStatus.UNKNOWN


def test_currency_mismatch():
    checker = SpendingChecker()

    result = checker.check_spending(50000, 100000, "INR", "USD")

    assert result.status == CheckStatus.UNKNOWN


def test_missing_currency():
    checker = SpendingChecker()

    result = checker.check_spending(50000, 100000, None, "INR")

    assert result.status == CheckStatus.UNKNOWN
