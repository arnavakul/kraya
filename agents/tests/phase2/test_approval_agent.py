
from unittest.mock import Mock

import pytest

from agents.approval_audit.agent import ApprovalAuditAgent
from schemas.approval import (
    ApprovalAction,
    ApprovalDecision,
    ApprovalRecord,
    ApprovalRequest,
    ApprovalStatus,
)


def create_request():
    return ApprovalRequest(
        organization_id="org-1",
        requester_user_id="user-1",
        action=ApprovalAction.SUPPLIER_SELECTION,
        entity_type="supplier",
        entity_id="supplier-1",
        reason="Supplier selection requires approval.",
    )


def create_record():
    return ApprovalRecord(
        id="approval-1",
        organization_id="org-1",
        requester_user_id="user-1",
        action=ApprovalAction.SUPPLIER_SELECTION,
        entity_type="supplier",
        entity_id="supplier-1",
        reason="Supplier selection requires approval.",
        status=ApprovalStatus.PENDING,
    )


def create_agent(repository=None, audit_service=None, reviewer=None):
    return ApprovalAuditAgent(
        approval_repository=repository or Mock(),
        audit_service=audit_service or Mock(),
        reviewer_authorization=reviewer or Mock(),
    )


def test_create_approval_request():
    repository = Mock()
    audit_service = Mock()
    repository.create_approval.return_value = create_record()

    agent = create_agent(repository, audit_service)

    record = agent.create_approval_request(create_request())

    assert record.status == ApprovalStatus.PENDING
    repository.create_approval.assert_called_once()
    audit_service.record_action.assert_called_once()


def test_human_can_approve_request():
    repository = Mock()
    audit_service = Mock()
    reviewer = Mock()

    repository.get_approval.return_value = create_record()

    approved_record = create_record().model_copy(
        update={
            "status": ApprovalStatus.APPROVED,
            "reviewer_user_id": "user-2",
        }
    )
    repository.update_decision.return_value = approved_record

    agent = create_agent(repository, audit_service, reviewer)

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.APPROVED,
        comments="Approved.",
    )

    result = agent.process_decision(decision, "org-1")

    assert result.status == ApprovalStatus.APPROVED

    reviewer.validate_reviewer.assert_called_once()
    repository.update_decision.assert_called_once()
    audit_service.record_action.assert_not_called()


def test_human_can_reject_request():
    repository = Mock()
    audit_service = Mock()
    reviewer = Mock()

    repository.get_approval.return_value = create_record()

    rejected_record = create_record().model_copy(
        update={"status": ApprovalStatus.REJECTED}
    )
    repository.update_decision.return_value = rejected_record

    agent = create_agent(repository, audit_service, reviewer)

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.REJECTED,
    )

    result = agent.process_decision(decision, "org-1")

    assert result.status == ApprovalStatus.REJECTED
    reviewer.validate_reviewer.assert_called_once()


def test_unauthorized_reviewer_cannot_approve():
    repository = Mock()
    reviewer = Mock()

    repository.get_approval.return_value = create_record()

    reviewer.validate_reviewer.side_effect = ValueError(
        "Reviewer does not have approval permission."
    )

    agent = create_agent(repository, reviewer=reviewer)

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.APPROVED,
    )

    with pytest.raises(ValueError, match="approval permission"):
        agent.process_decision(decision, "org-1")

    repository.update_decision.assert_not_called()


def test_requester_cannot_approve_own_request():
    repository = Mock()
    reviewer = Mock()

    repository.get_approval.return_value = create_record()

    reviewer.validate_reviewer.side_effect = ValueError(
        "Requester cannot approve their own request."
    )

    agent = create_agent(repository, reviewer=reviewer)

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-1",
        status=ApprovalStatus.APPROVED,
    )

    with pytest.raises(ValueError, match="own request"):
        agent.process_decision(decision, "org-1")

    repository.update_decision.assert_not_called()


def test_unknown_approval_is_rejected():
    repository = Mock()
    repository.get_approval.return_value = None

    agent = create_agent(repository)

    decision = ApprovalDecision(
        approval_id="unknown",
        reviewer_user_id="user-2",
        status=ApprovalStatus.APPROVED,
    )

    with pytest.raises(ValueError):
        agent.process_decision(decision, "org-1")


def test_wrong_organization_is_passed_to_repository():
    repository = Mock()
    repository.get_approval.return_value = None

    agent = create_agent(repository)

    decision = ApprovalDecision(
        approval_id="approval-1",
        reviewer_user_id="user-2",
        status=ApprovalStatus.APPROVED,
    )

    with pytest.raises(ValueError):
        agent.process_decision(decision, "wrong-org")

    repository.get_approval.assert_called_once_with(
        approval_id="approval-1",
        organization_id="wrong-org",
    )
