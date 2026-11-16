from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agents.evaluation.agent import EvaluationAgent
from agents.negotiations.agent import NegotiationAgent
from orchestration.graph import build_procurement_graph
from orchestration.inbox_triage_graph import build_inbox_triage_graph
from orchestration.procurement_inbox_handoff import (
    build_approved_rfq_inbox_context,
    build_inbox_triage_input,
)
from pydantic_models.email_classification import EmailClassification
from pydantic_models.email_message import EmailMessage
from pydantic_models.requirement import Requirement
from pydantic_models.rfq import RFQDraft, RFQDraftingResult
from pydantic_models.supplier_candidate import SupplierCandidate
from pydantic_models.supplier_discovery_result import (
    SupplierAssessment,
    SupplierDiscoveryResult,
)
from pydantic_models.supplier_match import SupplierMatch
from schemas.approval import ApprovalAction, ApprovalRecord, ApprovalStatus
from schemas.evaluation import ConstraintStatus, MLEvaluationStatus
from schemas.negotiation import CounterOffer
from schemas.policy import (
    CheckStatus,
    PolicyCheckResult,
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    RiskLevel,
)
from schemas.quotation import (
    DeliveryTimeUnit,
    Quotation,
    QuoteLineItem,
    ShippingStatus,
)
from services.financial_validator import ValidationReport, ValidationStatus
from tools.dispatch.dispatch_service import DispatchService
from tools.dispatch.mock_email_provider import MockEmailProvider


ORG_ID = "00000000-0000-4000-8000-000000000001"
SUPPLIER_ID = "00000000-0000-4000-8000-000000000002"
RFQ_ID = "00000000-0000-4000-8000-000000000003"
REQUESTER_ID = "requester-synthetic"
REVIEWER_ID = "reviewer-synthetic"
SUPPLIER_EMAIL = "sales@supplier.example.test"
SUPPLIER_NAME = "Synthetic Supplier"


def make_requirement(*, with_specs=True):
    return Requirement(
        product_service="Synthetic stainless steel containers",
        quantity=2,
        specifications=("stainless steel grade 304" if with_specs else None),
        delivery_location="Synthetic receiving dock",
        delivery_deadline=date.today() + timedelta(days=20),
        currency="INR",
        mandatory_constraints=(
            ["food-grade finish"] if with_specs else []
        ),
    )


def make_supplier():
    return SupplierCandidate(
        supplier_id=UUID(SUPPLIER_ID),
        organization_id=UUID("00000000-0000-4000-8000-000000000009"),
        name=SUPPLIER_NAME,
        contact_email=SUPPLIER_EMAIL,
        status="ACTIVE",
        categories=["containers"],
    )


def policy_request():
    return PolicyEvaluationRequest(
        organization_id=ORG_ID,
        user_id=REQUESTER_ID,
        action="CREATE_RFQ",
        user_role="ORG_ADMIN",
        user_status="ACTIVE",
        organization_status="ACTIVE",
        currency="INR",
    )


class FakePolicyAgent:
    def evaluate(self, request):
        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            risk_level=RiskLevel.LOW,
            checks=[PolicyCheckResult(
                check_name="synthetic_policy",
                status=CheckStatus.PASS,
                reason="Test-only synthetic policy allows this path.",
            )],
            reasons=["Test-only synthetic policy allows this path."],
        )

    def check_untrusted_message(self, message):
        return SimpleNamespace(
            status=SimpleNamespace(value="pass"),
            check_name="synthetic_message_check",
            reason="Synthetic test message passed screening.",
        )


class FakeApprovalAgent:
    requests = []
    decisions = []

    def create_approval_request(self, request):
        self.__class__.requests.append(request)
        return ApprovalRecord(
            id=f"approval-{request.entity_id}",
            organization_id=request.organization_id,
            requester_user_id=request.requester_user_id,
            action=request.action,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            reason=request.reason,
            evidence=request.evidence,
            status=ApprovalStatus.PENDING,
        )

    def process_decision(self, *, decision, organization_id):
        self.__class__.decisions.append((decision, organization_id))
        return ApprovalRecord(
            id=decision.approval_id,
            organization_id=organization_id,
            requester_user_id=REQUESTER_ID,
            action=ApprovalAction.SUPPLIER_SELECTION,
            entity_type="rfq",
            entity_id=RFQ_ID,
            reason="Synthetic test approval.",
            status=decision.status,
            reviewer_user_id=decision.reviewer_user_id,
            reviewer_comments=decision.comments,
        )


class FakeNegotiator:
    def generate_counteroffer(self, *, context, policy):
        return CounterOffer(
            proposed_price=Decimal("950"),
            proposed_quantity=context.current_quantity,
            proposed_delivery_days=context.delivery_days,
            proposed_delivery_unit=context.delivery_unit,
            negotiation_reason="Synthetic bounded proposal for review.",
            message_draft="Synthetic draft only; do not send.",
        )


class NoCallMLClient:
    async def health_check(self):
        raise AssertionError("Missing verified features must skip ML.")


class FakeExplainer:
    def explain(self, evaluation_data):
        names = [item["supplier_name"] for item in evaluation_data["suppliers"]]
        return {
            "supplier_strengths": {name: [] for name in names},
            "supplier_weaknesses": {name: [] for name in names},
            "trade_offs": {name: [] for name in names},
            "recommendation_summary": "Synthetic evaluation for review.",
            "recommendation_reasoning": ["Deterministic constraints evaluated."],
        }


class FakeDispatchRepository:
    def __init__(self):
        self.records = {}

    def create_dispatch(self, data):
        record = {**data, "dispatch_id": "dispatch-synthetic-1"}
        self.records[record["dispatch_id"]] = record
        return record

    def claim_dispatch(self, dispatch_id):
        return {"dispatch_id": dispatch_id}

    def update_status(self, **kwargs):
        return kwargs


class FakeInboxRepository:
    def claim_email(self, email):
        return True

    def complete_email(self, email_id, result):
        return True

    def fail_email(self, email_id, error_message):
        raise AssertionError(error_message)


class SyntheticReplyConnector:
    def __init__(self, email):
        self.email = email

    def fetch_emails(self):
        return [self.email]


def make_quotation(*, complete=True):
    return Quotation(
        supplier_name=SUPPLIER_NAME,
        supplier_email=SUPPLIER_EMAIL,
        quotation_number="SYN-QUOTE-1",
        issue_date=date.today(),
        valid_until=date.today() + timedelta(days=30),
        currency="INR",
        line_items=[QuoteLineItem(
            product_name="Synthetic stainless steel container",
            description=(
                "stainless steel grade 304; food-grade finish"
                if complete else None
            ),
            quantity=2,
            unit_price=500,
            line_total=1000,
        )],
        subtotal=1000,
        shipping_status=ShippingStatus.INCLUDED,
        grand_total=1000,
        delivery_time_days=10,
        delivery_time_unit=DeliveryTimeUnit.CALENDAR_DAYS,
        warranty_period="3 years",
        payment_terms="Net 30 days",
        additional_terms=(
            "stainless steel grade 304; food-grade finish"
            if complete else None
        ),
    )


def run_approved_procurement(monkeypatch, *, with_specs=True, decision="approve"):
    requirement = make_requirement(with_specs=with_specs)
    supplier = make_supplier()
    FakeApprovalAgent.requests = []
    FakeApprovalAgent.decisions = []

    from agents.policy_guardrails.agent import PolicyGuardrailsAgent
    from agents.approval_audit.agent import ApprovalAuditAgent
    import orchestration.nodes as nodes
    import orchestration.graph as graph_module

    monkeypatch.setattr(nodes, "run_intake_agent", lambda **kwargs: {
        "status": "validated",
        "requirement_draft": requirement.model_dump(mode="json"),
        "requirement": requirement.model_dump(mode="json"),
        "missing_fields": [],
        "clarification_questions": [],
        "errors": [],
    })
    discovery = SupplierDiscoveryResult(
        status="completed",
        total_candidates=1,
        suppliers=[SupplierAssessment(
            supplier=supplier,
            matching=SupplierMatch(
                supplier_id=supplier.supplier_id,
                supplier_name=supplier.name,
                overall_status="matched",
            ),
        )],
    )
    monkeypatch.setattr(
        nodes,
        "run_supplier_discovery_agent",
        lambda **kwargs: discovery,
    )
    rfq = RFQDraft(
        rfq_id=UUID(RFQ_ID),
        requirement=requirement,
        supplier=supplier,
        email_subject="Synthetic RFQ",
        email_body="Synthetic request for quotation.",
        status="pending_approval",
    )
    monkeypatch.setattr(
        nodes,
        "run_rfq_drafting_agent",
        lambda **kwargs: RFQDraftingResult(
            status="completed",
            total_suppliers=1,
            successful_drafts=1,
            rfq_drafts=[rfq],
        ),
    )
    monkeypatch.setattr(
        "agents.policy_guardrails.agent.PolicyGuardrailsAgent",
        lambda: FakePolicyAgent(),
    )
    monkeypatch.setattr(
        "agents.approval_audit.agent.ApprovalAuditAgent",
        FakeApprovalAgent,
    )

    graph = build_procurement_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "synthetic-workflow-thread"}}
    result = graph.invoke(
        {
            "user_input": "Synthetic procurement request.",
            "policy_evaluation_request": policy_request(),
        },
        config=config,
    )
    assert "__interrupt__" in result
    resumed = graph.invoke(
        Command(resume={"decisions": [{
            "rfq_id": RFQ_ID,
            "decision": decision,
            "reviewer_user_id": REVIEWER_ID,
            "comments": "Synthetic reviewer decision.",
        }]}),
        config=config,
    )
    return resumed, requirement


def test_synthetic_procurement_to_inbox_to_pending_negotiation_approval(monkeypatch):
    import agents.quote_extraction.agent as quote_agent_module
    import agents.inbox_triage.agent as inbox_agent_module

    approved_state, requirement = run_approved_procurement(monkeypatch)
    prior_decisions = list(FakeApprovalAgent.decisions)
    assert approved_state["workflow_status"] == "approved"
    assert approved_state["approved_rfq_contexts"][0]["reviewer_user_id"] == REVIEWER_ID
    assert approved_state["approved_rfq_contexts"][0]["organization_id"] == ORG_ID
    assert approved_state["approved_rfq_contexts"][0]["supplier"]["supplier_id"] == SUPPLIER_ID

    provider = MockEmailProvider()
    dispatch_repository = FakeDispatchRepository()
    dispatch = DispatchService(provider, dispatch_repository).dispatch_rfq(
        approved_state["rfq_drafts"][0]
    )
    assert dispatch["status"] == "sent"
    assert len(provider.sent_messages) == 1

    handoff = build_approved_rfq_inbox_context(
        approved_state,
        RFQ_ID,
        dispatch,
    )
    quote = make_quotation()
    monkeypatch.setattr(
        quote_agent_module,
        "extract_quotation",
        lambda text: quote,
    )
    monkeypatch.setattr(
        inbox_agent_module,
        "classify_email",
        lambda email, security_result: EmailClassification(
            category="quotation",
            confidence=0.99,
            summary="Synthetic quotation reply.",
            classification_source="llm",
        ),
    )
    reply = EmailMessage(
        email_id="synthetic-inbound-email-1",
        sender_email=SUPPLIER_EMAIL,
        sender_name=SUPPLIER_NAME,
        subject="Re: Synthetic RFQ",
        body="Synthetic quotation reply.",
        thread_id="synthetic-thread-1",
        in_reply_to=dispatch["provider_message_id"],
    )

    evaluation_agent = EvaluationAgent(
        ml_client=NoCallMLClient(),
        evaluation_repository=object(),
    )
    evaluation_agent.explainer = FakeExplainer()
    negotiation_agent = NegotiationAgent(negotiator=FakeNegotiator())
    policy_agent = FakePolicyAgent()
    approval_agent = FakeApprovalAgent()

    inbox_graph = build_inbox_triage_graph()
    inbox_input = build_inbox_triage_input(
        handoff,
        connector=SyntheticReplyConnector(reply),
        repository=FakeInboxRepository(),
        policy_guardrails_agent=policy_agent,
        evaluation_agent=evaluation_agent,
        negotiation_policies={SUPPLIER_NAME: {
            "target_price": "950",
            "minimum_acceptable_price": "900",
            "maximum_discount_percent": "10",
            "minimum_quantity": 1,
            "maximum_quantity": 5,
            "maximum_delivery_days": 15,
            "allowed_delivery_unit": "calendar_days",
            "requires_human_approval": True,
        }},
        negotiation_agent=negotiation_agent,
        approval_agent=approval_agent,
    )
    result = inbox_graph.invoke(inbox_input)

    assert result["inbox_triage_status"] == "completed"
    assert result["inbox_triage_result"].quotation_processing_results[0].status == "completed"
    evaluated = result["evaluation_result"].evaluations[0]
    assert evaluated.mandatory_constraints["technical_specifications"] == ConstraintStatus.PASS
    assert evaluated.eligible is True
    assert evaluated.ml_status == MLEvaluationStatus.SKIPPED_MISSING_FEATURES
    assert result["negotiation_status"] == "human_review_required"
    proposal = result["negotiation_results"][0]
    assert proposal["status"] == "approval_pending"
    assert proposal["negotiation_result"]["counter_offer"]["proposed_price"] == "950"
    assert proposal["approval_status"] == "pending"
    negotiation_approvals = [
        request for request in approval_agent.requests
        if request.action == ApprovalAction.SENSITIVE_ACTION
    ]
    assert len(negotiation_approvals) == 1
    assert negotiation_approvals[0].organization_id == ORG_ID
    assert negotiation_approvals[0].requester_user_id == REQUESTER_ID
    assert negotiation_approvals[0].entity_id == "synthetic-inbound-email-1"
    assert approval_agent.decisions == prior_decisions
    assert dispatch_repository.records
    assert requirement.specifications == "stainless steel grade 304"


def test_rejected_rfq_has_no_inbox_handoff(monkeypatch):
    rejected_state, _ = run_approved_procurement(monkeypatch, decision="reject")
    assert rejected_state["workflow_status"] == "rejected"
    assert rejected_state["approved_rfq_contexts"] == []
    with pytest.raises(ValueError, match="No human-approved RFQ"):
        build_approved_rfq_inbox_context(
            rejected_state,
            RFQ_ID,
            {"status": "sent", "provider_message_id": "synthetic-provider-id"},
        )


def test_missing_requirements_stay_unknown_and_supplier_ineligible(monkeypatch):
    approved_state, _ = run_approved_procurement(monkeypatch, with_specs=False)
    dispatch = {
        "status": "sent",
        "provider_message_id": "synthetic-provider-message",
    }
    handoff = build_approved_rfq_inbox_context(approved_state, RFQ_ID, dispatch)

    from orchestration.inbox_triage_nodes import evaluation_node
    from pydantic_models.inbox_triage_result import (
        InboxTriageRunResult,
        QuotationProcessingResult,
    )

    agent = EvaluationAgent(ml_client=NoCallMLClient(), evaluation_repository=object())
    agent.explainer = FakeExplainer()

    class AsyncEvaluationAgent:
        async def evaluate_suppliers_with_ml(self, quotations, required_specs=None, ml_context=None):
            return await agent.evaluate_suppliers_with_ml(
                quotations,
                required_specs=required_specs,
                ml_context=ml_context,
            )

    result = evaluation_node({
        "approved_rfq_context": handoff,
        "inbox_triage_result": InboxTriageRunResult(
            quotation_processing_results=[QuotationProcessingResult(
                email_id="synthetic-inbound-email-2",
                sender_email=SUPPLIER_EMAIL,
                status="completed",
                in_reply_to=dispatch["provider_message_id"],
                quotation=make_quotation().model_dump(mode="json"),
            )]
        ),
        "evaluation_agent": AsyncEvaluationAgent(),
    })
    evaluated = result["evaluation_result"].evaluations[0]
    assert evaluated.mandatory_constraints["technical_specifications"] == ConstraintStatus.UNKNOWN
    assert evaluated.eligible is False


def test_incomplete_quotation_is_not_evaluated(monkeypatch):
    approved_state, _ = run_approved_procurement(monkeypatch)
    handoff = build_approved_rfq_inbox_context(
        approved_state,
        RFQ_ID,
        {"status": "sent", "provider_message_id": "synthetic-provider-message"},
    )
    from orchestration.inbox_triage_nodes import evaluation_node
    from pydantic_models.inbox_triage_result import (
        InboxTriageRunResult,
        QuotationProcessingResult,
    )

    result = evaluation_node({
        "approved_rfq_context": handoff,
        "inbox_triage_result": InboxTriageRunResult(
            quotation_processing_results=[QuotationProcessingResult(
                email_id="synthetic-inbound-email-3",
                sender_email=SUPPLIER_EMAIL,
                status="needs_review",
                in_reply_to="synthetic-provider-message",
                quotation=make_quotation(complete=False).model_dump(mode="json"),
            )]
        ),
    })
    assert result["evaluation_status"] == "skipped_no_validated_quotations"
