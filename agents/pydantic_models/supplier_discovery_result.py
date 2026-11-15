
from pydantic import BaseModel, Field
from typing import Literal

from pydantic_models.supplier_candidate import SupplierCandidate
from pydantic_models.verification_evidence import VerificationEvidence
from pydantic_models.supplier_match import SupplierMatch


class SupplierAssessment(BaseModel):

    supplier: SupplierCandidate

    matching: SupplierMatch

    verification_evidence: list[VerificationEvidence] = Field(
        default_factory=list
    )

    verification_issues: list[str] = Field(
        default_factory=list
    )


class SupplierDiscoveryResult(BaseModel):

    status: Literal[
        "completed",
        "no_candidates",
        "failed"
    ]

    total_candidates: int = 0

    suppliers: list[SupplierAssessment] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )
