
import pytest

from agents.approval_audit.approval_checker import ApprovalChecker
from schemas.approval import (
    ApprovalRecord,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalAction,
    ApprovalStatus,
)


def create_record():
    request = ApprovalRequest(
        organization_id="org-1",
        requester_user_id="user-1",
        action=ApprovalAction.SUPPLIER_SELECTION,
        entity_type="supplier",
        entity_id="supplier-1",
        reason="Supplier selection requires approval.",
    )

    return ApprovalRecord(
        id="approval-1",
        **request.model_dump(),
    )


def test_valid_approval():
    record = create_record()

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.APPROVED,
    )

    ApprovalChecker().validate_decision(record, decision)


def test_requester_cannot_approve_own_request():
    record = create_record()

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-1",
        status=ApprovalStatus.APPROVED,
    )

    with pytest.raises(ValueError):
        ApprovalChecker().validate_decision(record, decision)


def test_rejected_decision_is_valid():
    record = create_record()

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.REJECTED,
    )

    ApprovalChecker().validate_decision(record, decision)


def test_already_reviewed_request_cannot_be_reviewed_again():
    record = create_record()
    record.status = ApprovalStatus.APPROVED

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.REJECTED,
    )

    with pytest.raises(ValueError):
        ApprovalChecker().validate_decision(record, decision)


def test_wrong_approval_id_is_rejected():
    record = create_record()

    decision = ApprovalDecision(
        approval_id="wrong-id",
        reviewer_user_id="user-2",
        status=ApprovalStatus.APPROVED,
    )

    with pytest.raises(ValueError):
        ApprovalChecker().validate_decision(record, decision)
