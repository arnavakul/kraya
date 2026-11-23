
from tools.supplier.supplier_matcher import match_supplier_requirements
from tools.supplier.supplier_verifier import verify_supplier
from tools.supplier.supplier_evidence import compile_supplier_evidence

from pydantic_models.supplier_discovery_result import (
    SupplierDiscoveryResult
)


def run_supplier_discovery_agent(
    requirement: dict,
    suppliers: list | None = None,
) -> SupplierDiscoveryResult:

    try:
        product_service = requirement.get("product_service")

        if not product_service:
            raise ValueError(
                "Product/service is required for supplier discovery."
            )

        # 1. Discover suppliers
        if not suppliers:
            from tools.supplier.supplier_search import search_suppliers
            suppliers = search_suppliers(product_service=product_service, active_only=True)

        if not suppliers:
            return SupplierDiscoveryResult(
                status="no_candidates",
                total_candidates=0,
                suppliers=[],
                warnings=["No matching suppliers found."]
            )

        assessments = []
        warnings = []

        # 2. Process each supplier
        for supplier in suppliers:

            # Requirement matching
            matching = match_supplier_requirements(
                supplier,
                requirement
            )

            # Supplier verification
            evidence = verify_supplier(supplier)

            # Evidence compilation
            assessment = compile_supplier_evidence(
                supplier,
                matching,
                evidence
            )

            assessments.append(assessment)

            warnings.extend(
                assessment.verification_issues
            )

        # 3. Return structured result
        return SupplierDiscoveryResult(
            status="completed",
            total_candidates=len(assessments),
            suppliers=assessments,
            warnings=list(dict.fromkeys(warnings))
        )

    except Exception as error:

        return SupplierDiscoveryResult(
            status="failed",
            total_candidates=0,
            suppliers=[],
            warnings=[str(error)]
        )
