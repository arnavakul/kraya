
from agents.inbox_triage.agent import run_inbox_triage_agent

from orchestration.inbox_triage_state import InboxTriageState


def inbox_triage_node(state: InboxTriageState) -> dict:

    try:

        result = run_inbox_triage_agent(
            connector=state.get("connector"),
            repository=state.get("repository")
        )

        if result.total_failed == 0:
            status = "completed"

        elif result.total_processed > 0 or result.total_skipped > 0:
            status = "partial"

        else:
            status = "failed"

        return {
            "inbox_triage_result": result,
            "inbox_triage_status": status,
            "errors": [
                item.error for item in result.failed_emails
            ]
        }

    except Exception as error:

        return {
            "inbox_triage_status": "failed",
            "errors": [str(error)]
        }
