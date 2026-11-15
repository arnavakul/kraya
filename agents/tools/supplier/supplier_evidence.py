
from pydantic_models.supplier_discovery_result import (
    SupplierAssessment
)


def compile_supplier_evidence(
    supplier,
    matching,
    verification_evidence
) -> SupplierAssessment:

    issues = []

    for evidence in verification_evidence:

        if evidence.verification_status in [
            "unverified",
            "inconsistent",
            "expired",
            "not_available"
        ]:
            issues.append(
                f"{evidence.field}: {evidence.notes}"
            )

    return SupplierAssessment(
        supplier=supplier,
        matching=matching,
        verification_evidence=verification_evidence,
        verification_issues=issues
    )
