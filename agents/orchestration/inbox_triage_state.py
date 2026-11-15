
from typing import TypedDict, Any, Optional

from pydantic_models.inbox_triage_result import (
    InboxTriageRunResult
)


class InboxTriageState(TypedDict, total=False):

    # Runtime dependencies (mock or real implementations)
    connector: Any
    repository: Any

    # Workflow output
    inbox_triage_result: Optional[InboxTriageRunResult]

    # Workflow tracking
    inbox_triage_status: str
    errors: list[str]

