
from typing import TypedDict, Any, Optional

from pydantic_models.inbox_triage_result import (
    InboxTriageRunResult
)
from schemas.policy import PolicyEvaluationRequest


class InboxTriageState(TypedDict, total=False):

    # Runtime dependencies (mock or real implementations)
    connector: Any
    repository: Any
    quote_extraction_agent: Any
    supplier_intent_agent: Any
    evaluation_agent: Any
    policy_guardrails_agent: Any
    negotiation_agent: Any
    approval_agent: Any
    policy_evaluation_request: Optional[PolicyEvaluationRequest]
    negotiation_policies: dict[str, dict]
    approved_rfq_context: Optional[dict]

    # Optional independently verified metadata, keyed by the extracted
    # supplier name and consumed only by Agent 8's existing feature builder.
    evaluation_ml_context: dict[str, dict]

    # Workflow output
    inbox_triage_result: Optional[InboxTriageRunResult]
    evaluation_result: Any
    evaluation_source_messages: list[dict]
    evaluation_status: str
    negotiation_results: list[dict]
    negotiation_approval_records: list[dict]
    negotiation_status: str

    # Workflow tracking
    inbox_triage_status: str
    errors: list[str]

