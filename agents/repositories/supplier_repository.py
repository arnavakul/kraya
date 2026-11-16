
from typing import Optional

from supabase import Client

from core.supabase import supabase


class SupplierRepository:
    """
    Handles database operations related to suppliers.
    All supplier queries are scoped to an organization.
    """

    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase

    def get_suppliers(
        self,
        organization_id: str,
        active_only: bool = True,
    ) -> list[dict]:
        """
        Fetch suppliers belonging to an organization.
        By default, only ACTIVE suppliers are returned.
        """

        query = (
            self.client
            .table("suppliers")
            .select("*")
            .eq("organization_id", organization_id)
        )

        if active_only:
            query = query.eq("status", "ACTIVE")

        response = query.order("name").execute()

        return response.data or []

    def get_supplier_by_id(
        self,
        supplier_id: str,
        organization_id: str,
    ) -> Optional[dict]:
        """
        Fetch one supplier using its ID and organization ID.
        """

        response = (
            self.client
            .table("suppliers")
            .select("*")
            .eq("id", supplier_id)
            .eq("organization_id", organization_id)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None

    def get_supplier_categories(
        self,
        supplier_id: str,
    ) -> list[str]:
        """
        Fetch all categories associated with a supplier.
        """

        response = (
            self.client
            .table("supplier_categories")
            .select("category")
            .eq("supplier_id", supplier_id)
            .execute()
        )

        return [item["category"] for item in response.data or []]

    def get_suppliers_by_category(
        self,
        organization_id: str,
        category: str,
    ) -> list[dict]:
        """
        Fetch ACTIVE suppliers in an organization
        that belong to a particular category.
        """

        category_response = (
            self.client
            .table("supplier_categories")
            .select("supplier_id")
            .ilike("category", category)
            .execute()
        )

        supplier_ids = [
            item["supplier_id"]
            for item in category_response.data or []
        ]

        if not supplier_ids:
            return []

        response = (
            self.client
            .table("suppliers")
            .select("*")
            .eq("organization_id", organization_id)
            .eq("status", "ACTIVE")
            .in_("id", supplier_ids)
            .order("name")
            .execute()
        )

        return response.data or []
