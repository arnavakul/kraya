
from typing import TypedDict, Optional


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

    # Workflow tracking
    current_agent: str
    workflow_status: str
    errors: list[str]
