from datetime import date, timedelta
from decimal import Decimal

from orchestration.negotiation import negotiation_node
from pydantic_models.inbox_triage_result import (
    InboxTriageRunResult,
    QuotationProcessingResult,
)
from schemas.approval import ApprovalStatus
from schemas.evaluation import (
    ConstraintStatus,
    EvaluationResult,
    SupplierEvaluation,
)
from schemas.negotiation import (
    CounterOffer,
    NegotiationAction,
    NegotiationContext,
    NegotiationPolicy,
    NegotiationResult,
    NegotiationStatus,
)
from schemas.policy import (
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    RiskLevel,
)


def make_quote(name="Synthetic Supplier"):
    return {
        "supplier_name": name,
        "supplier_email": "supplier@example.test",
        "quotation_number": "SUPPLIER-QUOTE-17",
        "issue_date": date.today().isoformat(),
        "valid_until": (date.today() + timedelta(days=30)).isoformat(),
        "currency": "INR",
        "line_items": [
            {
                "product_name": "Synthetic item",
                "quantity": "2",
                "unit_price": "500",
                "line_total": "1000",
            }
        ],
        "subtotal": "1000",
        "grand_total": "1000",
        "delivery_time_days": 10,
        "delivery_time_unit": "calendar_days",
        "payment_terms": "Net 30 days",
        "warranty_period": "2 years",
        "additional_terms": "Synthetic quotation terms.",
    }


def evaluation(name="Synthetic Supplier", eligible=True):
    return SupplierEvaluation(
        supplier_name=name,
        mandatory_constraints={"synthetic_requirement": ConstraintStatus.PASS},
        eligible=eligible,
        weighted_score=91,
    )


def base_state(*, eligible=True, policy_decision=PolicyDecision.ALLOW):
    quote = make_quote()
    email_result = QuotationProcessingResult(
        email_id="synthetic-email-17",
        thread_id="synthetic-thread-17",
        sender_email="supplier@example.test",
        status="completed",
        quotation=quote,
    )
    return {
        "inbox_triage_result": InboxTriageRunResult(
            quotation_processing_results=[email_result]
        ),
        "evaluation_result": EvaluationResult(
            evaluations=[evaluation(eligible=eligible)]
        ),
        "policy_evaluation_request": PolicyEvaluationRequest(
            organization_id="org-synthetic",
            user_id="requester-synthetic",
            action="NEGOTIATE_COUNTEROFFER",
            user_role="ORG_ADMIN",
            user_status="ACTIVE",
            organization_status="ACTIVE",
            supplier_status="ACTIVE",
        ),
        "policy_guardrails_agent": FixedPolicyAgent(policy_decision),
    }


class FixedPolicyAgent:
    def __init__(self, decision):
        self.decision = decision
        self.calls = []

    def evaluate(self, request):
        self.calls.append(request)
        return PolicyEvaluationResult(
            decision=self.decision,
            risk_level=(
                RiskLevel.LOW if self.decision == PolicyDecision.ALLOW
                else RiskLevel.HIGH if self.decision == PolicyDecision.BLOCK
                else RiskLevel.MEDIUM
            ),
            reasons=["Synthetic policy result."],
            requires_human_review=self.decision == PolicyDecision.ESCALATE,
        )


class RecordingNegotiationAgent:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or NegotiationResult(
            supplier_name="Synthetic Supplier",
            status=NegotiationStatus.APPROVAL_REQUIRED,
            recommended_action=NegotiationAction.COUNTEROFFER,
            counter_offer=CounterOffer(
                proposed_price=Decimal("950"),
                negotiation_reason="Synthetic proposal.",
                message_draft="Synthetic message draft; do not send.",
            ),
            approval_reasons=["Human review required."],
            requires_human_approval=True,
        )

    def process_negotiation(self, context, policy, supplier_evaluation=None):
        self.calls.append((context, policy, supplier_evaluation))
        return self.result


class FakeApprovalAgent:
    def __init__(self):
        self.requests = []
        self.decisions = []

    def create_approval_request(self, request):
        self.requests.append(request)
        from schemas.approval import ApprovalRecord

        return ApprovalRecord(
            id="approval-synthetic-17",
            organization_id=request.organization_id,
            requester_user_id=request.requester_user_id,
            action=request.action,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            reason=request.reason,
            evidence=request.evidence,
            status=ApprovalStatus.PENDING,
        )

    def process_decision(self, **kwargs):
        self.decisions.append(kwargs)
        raise AssertionError("Negotiation node must not decide approvals.")


def complete_policy():
    return {
        "target_price": "950",
        "minimum_acceptable_price": "900",
        "maximum_discount_percent": "10",
        "minimum_quantity": 1,
        "maximum_quantity": 5,
        "maximum_delivery_days": 15,
        "allowed_delivery_unit": "calendar_days",
        "requires_human_approval": True,
    }


def test_eligible_supplier_reaches_agent9_with_actual_quote_context():
    state = base_state()
    agent = RecordingNegotiationAgent()
    state.update({
        "negotiation_agent": agent,
        "negotiation_policies": {"Synthetic Supplier": complete_policy()},
        "approval_agent": FakeApprovalAgent(),
    })

    result = negotiation_node(state)

    assert len(agent.calls) == 1
    context, policy, supplier_evaluation = agent.calls[0]
    assert context.current_price == Decimal("1000")
    assert context.current_quantity == 2
    assert context.delivery_days == 10
    assert context.payment_terms == "Net 30 days"
    assert policy.minimum_acceptable_price == Decimal("900")
    assert supplier_evaluation.eligible is True
    assert result["negotiation_results"][0]["status"] == "approval_pending"


def test_ineligible_supplier_cannot_enter_negotiation():
    state = base_state(eligible=False)
    agent = RecordingNegotiationAgent()
    state["negotiation_agent"] = agent

    result = negotiation_node(state)

    assert agent.calls == []
    assert result["negotiation_status"] == "skipped_no_eligible_suppliers"


def test_agent9_direct_call_rejects_an_ineligible_agent8_result():
    from agents.negotiations.agent import NegotiationAgent

    class MustNotNegotiate:
        def generate_counteroffer(self, context, policy):
            raise AssertionError("Ineligible supplier reached offer generation")

    agent = NegotiationAgent(negotiator=MustNotNegotiate())
    context = NegotiationContext(
        supplier_name="Synthetic Supplier",
        current_price=Decimal("1000"),
    )
    result = agent.process_negotiation(
        context=context,
        policy=NegotiationPolicy(
            minimum_acceptable_price=Decimal("900"),
        ),
        supplier_evaluation=evaluation(eligible=False),
    )
    assert result.status == NegotiationStatus.REJECTED
    assert result.recommended_action == NegotiationAction.NO_ACTION


def test_agent9_offer_calculator_respects_discount_and_minimum_price():
    from agents.negotiations.agent import NegotiationAgent

    class FixedNegotiator:
        def generate_counteroffer(self, context, policy):
            return CounterOffer(
                proposed_price=Decimal("900"),
                proposed_quantity=2,
                proposed_delivery_days=10,
                proposed_delivery_unit="calendar_days",
                negotiation_reason="Within synthetic limits.",
                message_draft="Synthetic draft only.",
            )

    state = base_state()
    state.update({
        "negotiation_agent": NegotiationAgent(negotiator=FixedNegotiator()),
        "negotiation_policies": {"Synthetic Supplier": complete_policy()},
        "approval_agent": FakeApprovalAgent(),
    })
    result = negotiation_node(state)

    negotiation = result["negotiation_results"][0]["negotiation_result"]
    assert negotiation["policy_violations"] == []
    assert Decimal(negotiation["counter_offer"]["proposed_price"]) >= Decimal("900")
    assert result["negotiation_results"][0]["approval_status"] == "pending"


def test_missing_commercial_limits_require_review_without_calling_agent9():
    state = base_state()
    agent = RecordingNegotiationAgent()
    state.update({
        "negotiation_agent": agent,
        "negotiation_policies": {
            "Synthetic Supplier": {"minimum_acceptable_price": "900"}
        },
    })

    result = negotiation_node(state)

    assert agent.calls == []
    assert result["negotiation_results"][0]["status"] == "insufficient_information"
    assert result["negotiation_results"][0]["requires_human_review"] is True


def test_policy_block_stops_before_agent9_and_approval():
    state = base_state(policy_decision=PolicyDecision.BLOCK)
    agent = RecordingNegotiationAgent()
    approvals = FakeApprovalAgent()
    state.update({
        "negotiation_agent": agent,
        "approval_agent": approvals,
        "negotiation_policies": {"Synthetic Supplier": complete_policy()},
    })

    result = negotiation_node(state)

    assert agent.calls == []
    assert approvals.requests == []
    assert result["negotiation_results"][0]["status"] == "policy_blocked"


def test_policy_escalation_requires_pending_human_review():
    state = base_state(policy_decision=PolicyDecision.ESCALATE)
    agent = RecordingNegotiationAgent()
    approvals = FakeApprovalAgent()
    state.update({"negotiation_agent": agent, "approval_agent": approvals})

    result = negotiation_node(state)

    assert agent.calls == []
    assert len(approvals.requests) == 1
    assert approvals.requests[0].action.value == "policy_exception"
    assert result["negotiation_results"][0]["approval_status"] == "pending"


def test_counteroffer_approval_stays_pending_and_is_never_sent():
    state = base_state()
    agent = RecordingNegotiationAgent()
    approvals = FakeApprovalAgent()
    state.update({
        "negotiation_agent": agent,
        "approval_agent": approvals,
        "negotiation_policies": {"Synthetic Supplier": complete_policy()},
    })

    result = negotiation_node(state)

    assert len(approvals.requests) == 1
    assert approvals.requests[0].action.value == "sensitive_action"
    assert result["negotiation_results"][0]["approval_status"] == "pending"
    assert approvals.decisions == []
    assert "Synthetic message draft; do not send." in result["negotiation_results"][0]["negotiation_result"]["counter_offer"]["message_draft"]
