
from schemas.policy import (
    CheckStatus,
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    RiskLevel,
    PolicyCheckResult,
)

from agents.policy_guardrails.permission_checker import PermissionChecker
from agents.policy_guardrails.spending_checker import SpendingChecker
from agents.policy_guardrails.supplier_checker import SupplierChecker
from agents.policy_guardrails.injection_detector import InjectionDetector


class PolicyGuardrailsAgent:
    """Coordinates procurement policy and security checks."""

    def __init__(self):
        self.permission_checker = PermissionChecker()
        self.spending_checker = SpendingChecker()
        self.supplier_checker = SupplierChecker()
        self.injection_detector = InjectionDetector()

    def check_untrusted_message(self, message: str | None) -> PolicyCheckResult:
        """Screen inbound text before it is passed to an LLM workflow."""
        return self.injection_detector.check_message(message)

    def evaluate(self, request: PolicyEvaluationRequest) -> PolicyEvaluationResult:
        checks = []

        # 1. Check user and organization eligibility.
        permission_result = self.permission_checker.check_permission(
            user_role=request.user_role,
            user_status=request.user_status,
            organization_status=request.organization_status,
            action=request.action,
        )
        checks.append(permission_result)

        # Role-specific authorization is not implemented yet.
        # Never treat account eligibility as action authorization.
        checks.append(
            PolicyCheckResult(
                check_name="role_authorization",
                status=CheckStatus.UNKNOWN,
                reason="Role-to-action permissions have not yet been configured.",
            )
        )

        # 2. Check spending when a procurement amount is supplied.
        if request.amount is not None or request.spending_limit is not None:
            checks.append(
                self.spending_checker.check_spending(
                    amount=request.amount,
                    spending_limit=request.spending_limit,
                    currency=request.currency,
                    spending_limit_currency=request.spending_limit_currency,
                )
            )

        # 3. Check supplier when supplier information is supplied.
        if request.supplier_status is not None:
            checks.append(
                self.supplier_checker.check_supplier(
                    request.supplier_status
                )
            )

        # 4. Inspect untrusted supplier content when supplied.
        if request.untrusted_message is not None:
            checks.append(
                self.check_untrusted_message(
                    request.untrusted_message
                )
            )

        failed_checks = [
            check for check in checks
            if check.status == CheckStatus.FAIL
        ]

        unknown_checks = [
            check for check in checks
            if check.status == CheckStatus.UNKNOWN
        ]

        reasons = [check.reason for check in checks]

        # A failed security or policy check blocks the action.
        if failed_checks:
            decision = PolicyDecision.BLOCK
            risk_level = RiskLevel.CRITICAL if any(
                check.check_name == "prompt_injection"
                for check in failed_checks
            ) else RiskLevel.HIGH

        # Missing evidence requires human review.
        elif unknown_checks:
            decision = PolicyDecision.ESCALATE
            risk_level = RiskLevel.MEDIUM

        else:
            decision = PolicyDecision.ALLOW
            risk_level = RiskLevel.LOW

        return PolicyEvaluationResult(
            decision=decision,
            risk_level=risk_level,
            checks=checks,
            reasons=reasons,
            requires_human_review=(
                decision == PolicyDecision.ESCALATE
            ),
        )
