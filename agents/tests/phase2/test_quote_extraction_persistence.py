
from unittest.mock import Mock

from agents.quote_extraction.agent import QuoteExtractionAgent
from schemas.quotation import Quotation
from services.financial_validator import (
    ValidationReport,
    ValidationStatus,
)


def test_process_and_save(monkeypatch):
    mock_repository = Mock()

    agent = QuoteExtractionAgent(
        quotation_repository=mock_repository
    )

    quotation = Quotation(
        supplier_name="Demo Supplier",
        currency="INR",
    )

    validation_report = ValidationReport(
        status=ValidationStatus.VALID,
        errors=[],
        warnings=[],
    )

    monkeypatch.setattr(
        agent,
        "process_document",
        lambda file_path: {
            "quotation": quotation,
            "validation_report": validation_report,
        },
    )

    mock_repository.save_quotation.return_value = {
        "id": "mock-quote-id"
    }

    result = agent.process_and_save(
        file_path="sample.pdf",
        organization_id="mock-org-id",
        supplier_id="mock-supplier-id",
        procurement_request_id="mock-request-id",
    )

    assert result["quotation_id"] == "mock-quote-id"

    mock_repository.save_quotation.assert_called_once()

    saved_arguments = (
        mock_repository.save_quotation.call_args.kwargs
    )

    assert saved_arguments["organization_id"] == "mock-org-id"
    assert saved_arguments["supplier_id"] == "mock-supplier-id"
    assert saved_arguments["procurement_request_id"] == "mock-request-id"
    assert saved_arguments["financial_validation"]["status"] == "VALID"
