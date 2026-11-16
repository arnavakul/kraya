
from unittest.mock import Mock

import pytest

from repositories.approval_repository import ApprovalRepository
from schemas.approval import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalAction,
    ApprovalStatus,
)


def sample_request():
    return ApprovalRequest(
        organization_id="org-1",
        requester_user_id="user-1",
        action=ApprovalAction.SUPPLIER_SELECTION,
        entity_type="supplier",
        entity_id="supplier-1",
        reason="Supplier selection needs approval.",
    )


def sample_database_record():
    return {
        "id": "approval-1",
        "organization_id": "org-1",
        "requester_user_id": "user-1",
        "reviewer_user_id": None,
        "action": "supplier_selection",
        "entity_type": "supplier",
        "entity_id": "supplier-1",
        "reason": "Supplier selection needs approval.",
        "evidence": [],
        "status": "PENDING",
        "reviewer_comments": None,
        "created_at": "2026-11-16T10:00:00+00:00",
        "reviewed_at": None,
    }


def test_create_approval():
    client = Mock()
    client.table.return_value.insert.return_value.execute.return_value.data = [
        sample_database_record()
    ]

    repository = ApprovalRepository(client=client)
    result = repository.create_approval(sample_request())

    assert result.status == ApprovalStatus.PENDING
    client.table.assert_called_with("approval_requests")


def test_get_approval():
    client = Mock()
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        sample_database_record()
    ]

    repository = ApprovalRepository(client=client)
    result = repository.get_approval("approval-1", "org-1")

    assert result.id == "approval-1"


def test_get_approval_returns_none_when_missing():
    client = Mock()
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

    repository = ApprovalRepository(client=client)
    result = repository.get_approval("missing", "org-1")

    assert result is None


def test_update_approval_decision():
    client = Mock()

    updated_record = sample_database_record()
    updated_record.update({
        "status": "APPROVED",
        "reviewer_user_id": "user-2",
        "reviewer_comments": "Approved.",
        "reviewed_at": "2026-11-16T10:30:00+00:00",
    })

    client.rpc.return_value.execute.return_value.data = updated_record

    repository = ApprovalRepository(client=client)

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.APPROVED,
        comments="Approved.",
    )

    result = repository.update_decision(decision, "org-1")

    assert result.status == ApprovalStatus.APPROVED
    client.rpc.assert_called_once_with(
        "kraya_process_approval_decision",
        {
            "p_approval_id": "approval-1",
            "p_organization_id": "org-1",
            "p_reviewer_user_id": "user-2",
            "p_decision_status": "APPROVED",
            "p_reviewer_comments": "Approved.",
        },
    )


def test_update_fails_if_request_is_not_pending():
    client = Mock()
    client.rpc.return_value.execute.return_value.data = None

    repository = ApprovalRepository(client=client)

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.APPROVED,
    )

    with pytest.raises(ValueError):
        repository.update_decision(decision, "org-1")
