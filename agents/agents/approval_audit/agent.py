
from agents.approval_audit.approval_checker import ApprovalChecker
from repositories.approval_repository import ApprovalRepository
from services.audit_service import AuditService
from agents.approval_audit.reviewer_authorization import (
    ReviewerAuthorizationChecker,
)
from schemas.approval import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalRequest,
    ApprovalStatus,
)


class ApprovalAuditAgent:
    """Manages persistent human approvals and audit logging."""

    def __init__(
        self,
        approval_checker=None,
        approval_repository=None,
        audit_service=None,
        reviewer_authorization=None
    ):
        self.approval_checker = approval_checker or ApprovalChecker()
        self.approval_repository = (
            approval_repository or ApprovalRepository()
        )
        self.audit_service = audit_service or AuditService()
        self.reviewer_authorization = (
            reviewer_authorization or ReviewerAuthorizationChecker()
        )

    def create_approval_request(
        self,
        request: ApprovalRequest,
    ) -> ApprovalRecord:

        # Save the approval request permanently in Supabase.
        record = self.approval_repository.create_approval(request)

        # Record the creation in the audit log.
        self.audit_service.record_action(
            organization_id=record.organization_id,
            actor_user_id=record.requester_user_id,
            action="APPROVAL_REQUESTED",
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            correlation_id=record.id,
            new_state=ApprovalStatus.PENDING.value,
            result="SUCCESS",
        )

        return record

    
    def process_decision(
        self,
        decision: ApprovalDecision,
        organization_id: str,
    ) -> ApprovalRecord:

        # Fetch the approval within the specified organization.
        record = self.approval_repository.get_approval(
            approval_id=decision.approval_id,
            organization_id=organization_id,
        )

        if record is None:
            raise ValueError(
                "Approval request was not found or is not accessible."
            )

        # Verify reviewer authorization.
        self.reviewer_authorization.validate_reviewer(
            reviewer_user_id=decision.reviewer_user_id,
            organization_id=record.organization_id,
            requester_user_id=record.requester_user_id,
        )

        # Validate the human decision.
        self.approval_checker.validate_decision(record, decision)

        # RPC atomically updates the approval and inserts its audit event.
        updated_record = self.approval_repository.update_decision(
            decision=decision,
            organization_id=organization_id,
        )

        return updated_record


    def get_approval(
        self,
        approval_id: str,
        organization_id: str,
    ):
        return self.approval_repository.get_approval(
            approval_id=approval_id,
            organization_id=organization_id,
        )

    def get_pending_approvals(
        self,
        organization_id: str,
    ) -> list[ApprovalRecord]:
        return self.approval_repository.get_pending_approvals(
            organization_id=organization_id,
        )
