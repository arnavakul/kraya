
from typing import Optional
from uuid import uuid4

from supabase import Client

from core.supabase import supabase
from schemas.quotation import Quotation


class QuotationRepository:
    """Handles quotation storage in Supabase."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase

    def save_quotation(
        self,
        organization_id: str,
        supplier_id: str,
        procurement_request_id: str,
        quotation: Quotation,
        financial_validation: dict,
    ) -> dict:

        if not quotation.currency:
            raise ValueError(
                "Quotation currency is required before saving."
            )

        record = {
            "id": str(uuid4()),
            "organization_id": organization_id,
            "supplier_id": supplier_id,
            "procurement_request_id": procurement_request_id,
            "quotation_number": quotation.quotation_number,
            "issue_date": (
                quotation.issue_date.isoformat()
                if quotation.issue_date else None
            ),
            "valid_until": (
                quotation.valid_until.isoformat()
                if quotation.valid_until else None
            ),
            "currency": quotation.currency,
            "quotation_data": quotation.model_dump(mode="json"),
            "financial_validation": financial_validation,
            "extraction_status": "COMPLETED",
        }

        response = (
            self.client
            .table("quotations")
            .insert(record)
            .execute()
        )

        if not response.data:
            raise RuntimeError("Quotation could not be saved.")

        return response.data[0]

    def get_quotation_by_id(
        self,
        quotation_id: str,
        organization_id: str,
    ) -> Optional[dict]:

        response = (
            self.client
            .table("quotations")
            .select("*")
            .eq("id", quotation_id)
            .eq("organization_id", organization_id)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None

    def get_quotations_by_request(
        self,
        procurement_request_id: str,
        organization_id: str,
    ) -> list[dict]:

        response = (
            self.client
            .table("quotations")
            .select("*")
            .eq("procurement_request_id", procurement_request_id)
            .eq("organization_id", organization_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data or []
