
from pathlib import Path

from services.document_parser import DocumentParser
from services.financial_validator import (
    FinancialValidator,
    ValidationReport,
)

from agents.quote_extraction.extractor import extract_quotation
from repositories.quotation_repository import QuotationRepository
from schemas.quotation import Quotation


class QuoteExtractionAgent:
    """
    Main entry point for Kraya's Quote Extraction Agent.
    """

    def __init__(
        self,
        quotation_repository: QuotationRepository | None = None,
    ):
        self.document_parser = DocumentParser()
        self.financial_validator = FinancialValidator()
        self.quotation_repository = (
            quotation_repository or QuotationRepository()
        )

    def process_document(self, file_path: str | Path) -> dict:
        """
        Extracts a quotation and validates its financial details.
        Does not save anything to Supabase.
        """

        document_text = self.document_parser.extract_text(file_path)

        return self.process_text(document_text)

    def process_text(self, document_text: str) -> dict:
        """Extract and validate quotation text already in memory."""

        if not document_text or not document_text.strip():
            raise ValueError("Quotation document text cannot be empty.")

        quotation: Quotation = extract_quotation(document_text)

        validation_report = self.financial_validator.validate(
            quotation
        )

        return {
            "quotation": quotation,
            "validation_report": validation_report,
        }

    def process_and_save(
        self,
        file_path: str | Path,
        organization_id: str,
        supplier_id: str,
        procurement_request_id: str,
    ) -> dict:
        """
        Extracts, validates and saves a quotation to Supabase.
        """

        result = self.process_document(file_path)

        quotation = result["quotation"]
        validation_report: ValidationReport = result[
            "validation_report"
        ]

        validation_data = {
            "status": validation_report.status.value,
            "errors": validation_report.errors,
            "warnings": validation_report.warnings,
        }

        saved_record = self.quotation_repository.save_quotation(
            organization_id=organization_id,
            supplier_id=supplier_id,
            procurement_request_id=procurement_request_id,
            quotation=quotation,
            financial_validation=validation_data,
        )

        return {
            **result,
            "quotation_id": saved_record["id"],
            "saved_record": saved_record,
        }
