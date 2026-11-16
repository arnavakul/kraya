
from uuid import uuid4

from agents.approval_audit.approval_checker import ApprovalChecker
from repositories.audit_repository import AuditRepository

from schemas.approval import (
    ApprovalAction,
    ApprovalDecision,
    ApprovalRecord,
    ApprovalRequest,
    ApprovalStatus,
)


class ApprovalAuditAgent:
    """Coordinates human approval and audit logging."""

    def __init__(
        self,
        approval_checker=None,
        audit_repository=None,
    ):
        self.approval_checker = approval_checker or ApprovalChecker()
        self.audit_repository = audit_repository

        # Temporary in-memory storage.
        # Approval records disappear when the application restarts.
        self.approvals: dict[str, ApprovalRecord] = {}

    def create_approval_request(
        self,
        request: ApprovalRequest,
    ) -> ApprovalRecord:

        approval_id = str(uuid4())

        record = ApprovalRecord(
            id=approval_id,
            **request.model_dump(),
            status=ApprovalStatus.PENDING,
        )

        # Record the request before storing it.
        if self.audit_repository:
            self.audit_repository.log_event(
                organization_id=record.organization_id,
                actor_user_id=record.requester_user_id,
                action="APPROVAL_REQUESTED",
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                correlation_id=approval_id,
                new_state=ApprovalStatus.PENDING.value,
                result="SUCCESS",
            )

        self.approvals[approval_id] = record
        return record

    def process_decision(
        self,
        decision: ApprovalDecision,
    ) -> ApprovalRecord:

        record = self.approvals.get(decision.approval_id)

        if record is None:
            raise ValueError("Approval request was not found.")

        # Validate the human decision.
        self.approval_checker.validate_decision(record, decision)

        action = (
            "APPROVAL_APPROVED"
            if decision.status == ApprovalStatus.APPROVED
            else "APPROVAL_REJECTED"
        )

        # Write the audit event before changing the stored status.
        if self.audit_repository:
            self.audit_repository.log_event(
                organization_id=record.organization_id,
                actor_user_id=decision.reviewer_user_id,
                action=action,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                correlation_id=record.id,
                previous_state=record.status.value,
                new_state=decision.status.value,
                result="SUCCESS",
            )

        updated_record = record.model_copy(
            update={
                "status": decision.status,
                "reviewer_user_id": decision.reviewer_user_id,
                "reviewer_comments": decision.comments,
            }
        )

        self.approvals[record.id] = updated_record

        return updated_record

    def get_approval(self, approval_id: str):
        return self.approvals.get(approval_id)
