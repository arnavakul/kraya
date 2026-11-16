
from datetime import datetime, timezone
from typing import Optional

from supabase import Client

from core.supabase import supabase
from schemas.approval import (
    ApprovalRecord,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
)


class ApprovalRepository:
    """Handles persistent approval records in Supabase."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase

    @staticmethod
    def _to_model(data: dict) -> ApprovalRecord:
        """Convert database values into our Pydantic schema."""

        record = dict(data)
        record["status"] = record["status"].lower()

        return ApprovalRecord.model_validate(record)

    def create_approval(
        self,
        request: ApprovalRequest,
    ) -> ApprovalRecord:

        record = request.model_dump(mode="json")

        # Match the uppercase status constraint in Supabase.
        record["status"] = "PENDING"

        response = (
            self.client
            .table("approval_requests")
            .insert(record)
            .execute()
        )

        if not response.data:
            raise RuntimeError("Approval request could not be saved.")

        return self._to_model(response.data[0])

    def get_approval(
        self,
        approval_id: str,
        organization_id: str,
    ) -> Optional[ApprovalRecord]:

        response = (
            self.client
            .table("approval_requests")
            .select("*")
            .eq("id", approval_id)
            .eq("organization_id", organization_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return self._to_model(response.data[0])

    def get_pending_approvals(
        self,
        organization_id: str,
    ) -> list[ApprovalRecord]:

        response = (
            self.client
            .table("approval_requests")
            .select("*")
            .eq("organization_id", organization_id)
            .eq("status", "PENDING")
            .order("created_at", desc=True)
            .execute()
        )

        return [
            self._to_model(record)
            for record in (response.data or [])
        ]

    
    def update_decision(
        self,
        decision: ApprovalDecision,
        organization_id: str,
    ) -> ApprovalRecord:

        response = self.client.rpc(
            "kraya_process_approval_decision",
            {
                "p_approval_id": decision.approval_id,
                "p_organization_id": organization_id,
                "p_reviewer_user_id": decision.reviewer_user_id,
                "p_decision_status": decision.status.value.upper(),
                "p_reviewer_comments": decision.comments,
            },
        ).execute()

        if not response.data:
            raise ValueError(
                "Approval decision could not be processed."
            )

        record = response.data

        # Supabase may return JSONB as a dictionary.
        if isinstance(record, str):
            import json
            record = json.loads(record)

        return self._to_model(record)

