
import pytest

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from orchestration.state import ProcurementState
from orchestration.approval import rfq_approval_node


def build_test_graph():
    graph = StateGraph(ProcurementState)

    graph.add_node(
        "approval",
        lambda state: rfq_approval_node(
            state,
            approval_agent=FakeApprovalAgent(),
        ),
    )

    graph.add_edge(START, "approval")
    graph.add_edge("approval", END)

    return graph.compile(checkpointer=InMemorySaver())


def get_test_drafts():
    return [
        {
            "rfq_id": "rfq-001",
            "supplier": {"name": "Supplier A"},
            "email_subject": "RFQ for Laptops",
            "email_body": "Request for 20 laptops.",
            "status": "pending_approval"
        },
        {
            "rfq_id": "rfq-002",
            "supplier": {"name": "Supplier B"},
            "email_subject": "RFQ for Laptops",
            "email_body": "Request for 20 laptops.",
            "status": "pending_approval"
        }
    ]


def get_test_records():
    return [
        {
            "id": f"approval-{index:03d}",
            "organization_id": "org-test",
            "requester_user_id": "requester-test",
            "action": "supplier_selection",
            "entity_type": "rfq",
            "entity_id": f"rfq-{index:03d}",
            "reason": "Synthetic approval test.",
            "evidence": [],
            "status": "pending",
        }
        for index in (1, 2)
    ]


class FakeApprovalAgent:
    def process_decision(self, decision, organization_id):
        assert organization_id == "org-test"
        if decision.reviewer_user_id == "requester-test":
            raise ValueError("Requester cannot approve their own request.")
        return type("Processed", (), {"status": decision.status})()


def get_config():
    return {
        "configurable": {
            "thread_id": "approval-test-001"
        }
    }


def test_approval_workflow_pauses_for_human_input():
    graph = build_test_graph()

    result = graph.invoke(
        {
            "rfq_drafts": get_test_drafts(),
            "approval_records": get_test_records(),
        },
        config=get_config()
    )

    assert "__interrupt__" in result
    assert result["__interrupt__"][0].value["type"] == (
        "rfq_approval_required"
    )


def test_all_rfqs_can_be_approved():
    graph = build_test_graph()
    config = get_config()

    graph.invoke(
        {
            "rfq_drafts": get_test_drafts(),
            "approval_records": get_test_records(),
        },
        config=config
    )

    result = graph.invoke(
        Command(
            resume={
                "decisions": [
                    {"rfq_id": "rfq-001", "decision": "approve", "reviewer_user_id": "reviewer-test"},
                    {"rfq_id": "rfq-002", "decision": "approve", "reviewer_user_id": "reviewer-test"}
                ]
            }
        ),
        config=config
    )

    assert result["approval_status"] == "completed"
    assert result["approved_count"] == 2
    assert result["rejected_count"] == 0
    assert result["workflow_status"] == "approved"

    assert all(
        draft["status"] == "approved"
        for draft in result["rfq_drafts"]
    )


def test_all_rfqs_can_be_rejected():
    graph = build_test_graph()
    config = get_config()

    graph.invoke(
        {
            "rfq_drafts": get_test_drafts(),
            "approval_records": get_test_records(),
        },
        config=config
    )

    result = graph.invoke(
        Command(
            resume={
                "decisions": [
                    {"rfq_id": "rfq-001", "decision": "reject", "reviewer_user_id": "reviewer-test"},
                    {"rfq_id": "rfq-002", "decision": "reject", "reviewer_user_id": "reviewer-test"}
                ]
            }
        ),
        config=config
    )

    assert result["approval_status"] == "completed"
    assert result["approved_count"] == 0
    assert result["rejected_count"] == 2
    assert result["workflow_status"] == "rejected"


def test_mixed_approval_decisions():
    graph = build_test_graph()
    config = get_config()

    graph.invoke(
        {
            "rfq_drafts": get_test_drafts(),
            "approval_records": get_test_records(),
        },
        config=config
    )

    result = graph.invoke(
        Command(
            resume={
                "decisions": [
                    {"rfq_id": "rfq-001", "decision": "approve", "reviewer_user_id": "reviewer-test"},
                    {"rfq_id": "rfq-002", "decision": "reject", "reviewer_user_id": "reviewer-test"}
                ]
            }
        ),
        config=config
    )

    assert result["approved_count"] == 1
    assert result["rejected_count"] == 1
    assert result["workflow_status"] == "partially_approved"

    assert result["rfq_drafts"][0]["status"] == "approved"
    assert result["rfq_drafts"][1]["status"] == "rejected"


def test_invalid_decision_is_rejected():
    graph = build_test_graph()
    config = get_config()

    graph.invoke(
        {
            "rfq_drafts": get_test_drafts(),
            "approval_records": get_test_records(),
        },
        config=config
    )

    with pytest.raises(ValueError, match="Invalid decision"):
        graph.invoke(
            Command(
                resume={
                    "decisions": [
                        {"rfq_id": "rfq-001", "decision": "send", "reviewer_user_id": "reviewer-test"},
                        {"rfq_id": "rfq-002", "decision": "approve", "reviewer_user_id": "reviewer-test"}
                    ]
                }
            ),
            config=config
        )


def test_missing_decision_is_rejected():
    graph = build_test_graph()
    config = get_config()

    graph.invoke(
        {
            "rfq_drafts": get_test_drafts(),
            "approval_records": get_test_records(),
        },
        config=config
    )

    with pytest.raises(ValueError, match="every RFQ"):
        graph.invoke(
            Command(
                resume={
                    "decisions": [
                        {"rfq_id": "rfq-001", "decision": "approve", "reviewer_user_id": "reviewer-test"}
                    ]
                }
            ),
            config=config
        )
