
from typing import Optional
from supabase import Client

from core.supabase import supabase


class AuditRepository:
    """Stores procurement audit events in Supabase."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase

    def log_event(
        self,
        organization_id: str,
        actor_user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        correlation_id: Optional[str] = None,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        result: str = "SUCCESS",
    ) -> dict:
        """Insert an audit event. Existing events are never modified."""

        record = {
            "organization_id": organization_id,
            "actor_user_id": actor_user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "correlation_id": correlation_id,
            "previous_state": previous_state,
            "new_state": new_state,
            "result": result,
        }

        response = (
            self.client
            .table("audit_events")
            .insert(record)
            .execute()
        )

        if not response.data:
            raise RuntimeError("Audit event could not be saved.")

        return response.data[0]
