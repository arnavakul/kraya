
from schemas.approval import (
    ApprovalRecord,
    ApprovalDecision,
    ApprovalStatus,
)


class ApprovalChecker:

    def validate_decision(
        self,
        record: ApprovalRecord,
        decision: ApprovalDecision,
    ) -> None:

        if record.status != ApprovalStatus.PENDING:
            raise ValueError(
                "Only pending approval requests can be reviewed."
            )

        if decision.approval_id != record.id:
            raise ValueError(
                "Approval ID does not match the request."
            )

        if decision.reviewer_user_id == record.requester_user_id:
            raise ValueError(
                "A requester cannot approve their own request."
            )

        if decision.status not in {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
        }:
            raise ValueError(
                "Decision must be APPROVED or REJECTED."
            )

        if not decision.reviewer_user_id.strip():
            raise ValueError("Reviewer user ID is required.")
