
from agents.supplier_intent.analyzer import analyze_supplier_message
from repositories.inbox_repository import InboxRepository
from schemas.suppliers_intent import SupplierIntentAnalysis


class SupplierIntentAgent:
    """
    Kraya's Supplier Intent and Clarification Agent.
    """

    def __init__(self, inbox_repository=None):
        self.inbox_repository = (
            inbox_repository or InboxRepository()
        )

    def process_message(
        self,
        supplier_message: str,
        rfq_context: str = "",
        conversation_history: str = "",
    ) -> SupplierIntentAnalysis:

        return analyze_supplier_message(
            supplier_message=supplier_message,
            rfq_context=rfq_context,
            conversation_history=conversation_history,
        )

    def process_and_save(
        self,
        email_id: str,
        supplier_message: str,
        rfq_context: str = "",
        conversation_history: str = "",
    ) -> SupplierIntentAnalysis:
        """
        Analyze a supplier email and save its results to Supabase.
        """

        self.inbox_repository.update_processing_status(
            email_id=email_id,
            status="processing",
        )

        try:
            analysis = self.process_message(
                supplier_message=supplier_message,
                rfq_context=rfq_context,
                conversation_history=conversation_history,
            )

            saved_record = self.inbox_repository.save_analysis(
                email_id=email_id,
                analysis=analysis,
            )

            if saved_record is None:
                raise ValueError(
                    f"No inbox email found for email_id: {email_id}"
                )

            return analysis

        except Exception as error:
            self.inbox_repository.update_processing_status(
                email_id=email_id,
                status="failed",
                error=str(error),
            )
            raise
