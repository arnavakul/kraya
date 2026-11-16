
from typing import Optional

from supabase import Client

from core.supabase import supabase


class InboxRepository:
    """
    Handles database operations for supplier emails.
    """

    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase

    def get_email(self, email_id: str) -> Optional[dict]:
        """Fetch an email using its ID."""

        response = (
            self.client
            .table("inbox_emails")
            .select("*")
            .eq("email_id", email_id)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None

    def update_processing_status(
        self,
        email_id: str,
        status: str,
        error: Optional[str] = None,
    ) -> Optional[dict]:
        """Update the processing status of an email."""

        if status not in {"processing", "completed", "failed"}:
            raise ValueError("Invalid email processing status.")

        update_data = {
            "processing_status": status,
            "last_error": error,
        }

        response = (
            self.client
            .table("inbox_emails")
            .update(update_data)
            .eq("email_id", email_id)
            .execute()
        )

        return response.data[0] if response.data else None

    def save_analysis(
        self,
        email_id: str,
        analysis,
    ) -> Optional[dict]:
        """
        Save Agent 7's analysis using existing database columns.
        """

        update_data = {
            "category": analysis.intent.value,
            "summary": analysis.intent_summary,
            "routing_action": analysis.recommended_action.value,
            "requires_human_review": analysis.requires_human_review,
            "processing_status": "completed",
            "last_error": None,
        }

        response = (
            self.client
            .table("inbox_emails")
            .update(update_data)
            .eq("email_id", email_id)
            .execute()
        )

        return response.data[0] if response.data else None
