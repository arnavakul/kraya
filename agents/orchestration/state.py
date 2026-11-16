
from typing import TypedDict, Optional
from typing import Any

from schemas.policy import PolicyEvaluationRequest


class ProcurementState(TypedDict, total=False):

    # User input
    user_input: str

    # Intake Agent
    requirement_draft: Optional[dict]
    requirement: Optional[dict]
    missing_fields: list[str]
    clarification_questions: list[str]
    intake_errors: list[str]
    intake_status: str

    # Supplier Discovery Agent
    supplier_discovery_result: Optional[dict]
    supplier_candidates: list[dict]
    discovery_status: str

    # RFQ Drafting Agent
    rfq_drafting_result: Optional[dict]
    rfq_drafts: list[dict]
    rfq_drafting_status: str

    # Workflow tracking
    current_agent: str
    workflow_status: str
    errors: list[str]

    supplier_eligibility_results: list[dict]
    suppliers_requiring_review: list[dict]
    rfq_drafting_status: str
    
    # Human approval
    approval_decisions: Optional[dict]
    approval_status: str
    approved_count: int
    rejected_count: int

    # Runtime policy/approval dependencies and existing schema context.
    policy_evaluation_request: Optional[PolicyEvaluationRequest]
    policy_guardrails_agent: Any
    approval_agent: Any
    approval_action: str
    policy_results: list[dict]
    policy_decision: str
    policy_status: str
    approval_records: list[dict]
    approval_request_status: str
    approved_rfq_contexts: list[dict]
