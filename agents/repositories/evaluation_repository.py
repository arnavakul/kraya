
from typing import Optional

from supabase import Client

from core.supabase import supabase


class EvaluationRepository:
    """
    Handles database operations for supplier evaluation records.
    """

    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase

    def save_evaluation(
        self,
        supplier_id: str,
        quote_id: str,
        composite_score: float,
        baseline_score: Optional[float] = None,
        evaluation_id: Optional[str] = None,
    ) -> dict:
        """
        Save an evaluation result in Supabase.
        """

        import uuid

        record = {
            "id": evaluation_id or str(uuid.uuid4()),
            "supplier_id": supplier_id,
            "quote_id": quote_id,
            "composite_score": composite_score,
            "baseline_score": baseline_score,
        }

        response = (
            self.client
            .table("evaluation_records")
            .insert(record)
            .execute()
        )

        return response.data[0] if response.data else record

    def get_evaluations_by_supplier(
        self,
        supplier_id: str,
    ) -> list[dict]:
        """
        Fetch all evaluation records for a supplier.
        """

        response = (
            self.client
            .table("evaluation_records")
            .select("*")
            .eq("supplier_id", supplier_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data or []

    def get_evaluation_by_quote(
        self,
        quote_id: str,
    ) -> Optional[dict]:
        """
        Fetch the most recent evaluation for a quotation.
        """

        response = (
            self.client
            .table("evaluation_records")
            .select("*")
            .eq("quote_id", quote_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None
