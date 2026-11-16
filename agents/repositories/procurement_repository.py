
from typing import Optional

from supabase import Client

from core.supabase import supabase


class ProcurementRepository:
    """
    Handles database operations related to procurement requests
    and their line items.
    """

    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase

    def get_requests(
        self,
        organization_id: str,
        status: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetch procurement requests belonging to an organization.

        If status is provided, only requests with that status
        are returned.
        """

        query = (
            self.client
            .table("procurement_requests")
            .select("*")
            .eq("organization_id", organization_id)
        )

        if status:
            query = query.eq("status", status.upper())

        response = (
            query
            .order("created_at", desc=True)
            .execute()
        )

        return response.data or []

    def get_request_by_id(
        self,
        request_id: str,
        organization_id: str,
    ) -> Optional[dict]:
        """
        Fetch one procurement request and its associated items.
        """

        response = (
            self.client
            .table("procurement_requests")
            .select("*")
            .eq("id", request_id)
            .eq("organization_id", organization_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        procurement_request = response.data[0]

        items_response = (
            self.client
            .table("procurement_request_items")
            .select("*")
            .eq("request_id", request_id)
            .order("line_no")
            .execute()
        )

        procurement_request["items"] = items_response.data or []

        return procurement_request

    def get_request_items(
        self,
        request_id: str,
        organization_id: str,
    ) -> list[dict]:
        """
        Fetch line items only if the request belongs
        to the specified organization.
        """

        procurement_request = self.get_request_by_id(
            request_id=request_id,
            organization_id=organization_id,
        )

        if procurement_request is None:
            return []

        return procurement_request["items"]
