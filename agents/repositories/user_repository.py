
from typing import Optional

from supabase import Client
from core.supabase import supabase


class UserRepository:
    """Retrieves user information for authorization checks."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        response = (
            self.client
            .table("users")
            .select("id, organization_id, role, status")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None
