
from typing import Optional

from repositories.audit_repository import AuditRepository


class AuditService:
    """Provides a service interface for recording audit events."""

    def __init__(self, repository: Optional[AuditRepository] = None):
        self.repository = repository or AuditRepository()

    def record_action(
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

        return self.repository.log_event(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            correlation_id=correlation_id,
            previous_state=previous_state,
            new_state=new_state,
            result=result,
        )
