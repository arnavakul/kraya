
from pydantic_models.rfq import (
    RFQDraft,
    RFQDraftingResult
)

from tools.rfq.rfq_template import build_rfq_template
from tools.rfq.email_drafting_service import draft_rfq_email
from tools.rfq.rfq_validator import validate_rfq_content


def run_rfq_drafting_agent(
    requirement,
    suppliers: list
) -> RFQDraftingResult:

    drafts = []
    warnings = []
    failed_drafts = 0

    if not suppliers:
        return RFQDraftingResult(
            status="failed",
            total_suppliers=0,
            warnings=["No suppliers provided for RFQ drafting."]
        )

    for supplier in suppliers:

        try:
            # Step 1: Build canonical RFQ data
            rfq_data = build_rfq_template(
                requirement=requirement,
                supplier=supplier
            )

            # Step 2: Generate email using Gemini
            email_content = draft_rfq_email(rfq_data)

            # Step 3: Validate generated email
            validation = validate_rfq_content(
                rfq_data=rfq_data,
                email_content=email_content
            )

            if not validation["valid"]:
                failed_drafts += 1

                warnings.append(
                    f"{supplier.name}: RFQ validation failed: "
                    f"{validation['errors']}"
                )

                continue

            # Step 4: Create structured RFQ draft
            rfq = RFQDraft(
                requirement=requirement,
                supplier=supplier,
                email_subject=email_content["email_subject"],
                email_body=email_content["email_body"],
                status="pending_approval"
            )

            drafts.append(rfq)

        except Exception as error:

            failed_drafts += 1

            warnings.append(
                f"{supplier.name}: RFQ generation failed: {str(error)}"
            )

    successful_drafts = len(drafts)

    if failed_drafts == 0:
        status = "completed"
    elif successful_drafts > 0:
        status = "partial"
    else:
        status = "failed"

    return RFQDraftingResult(
        status=status,
        total_suppliers=len(suppliers),
        successful_drafts=successful_drafts,
        failed_drafts=failed_drafts,
        rfq_drafts=drafts,
        warnings=warnings
    )
