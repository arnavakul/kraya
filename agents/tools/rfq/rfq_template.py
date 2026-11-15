
from pydantic_models.requirement import Requirement
from pydantic_models.supplier_candidate import SupplierCandidate


def build_rfq_template(
    requirement: Requirement,
    supplier: SupplierCandidate
) -> dict:
    """
    Build the canonical RFQ content using approved
    procurement requirements and supplier information.
    """

    return {
        "supplier_name": supplier.name,
        "contact_name": supplier.contact_name,
        "contact_email": supplier.contact_email,

        "product_service": requirement.product_service,
        "quantity": requirement.quantity,
        "specifications": requirement.specifications,
        "quality_requirements": requirement.quality_requirements,

        "delivery_location": requirement.delivery_location,
        "delivery_deadline": (
            requirement.delivery_deadline.isoformat()
            if requirement.delivery_deadline
            else None
        ),

        "budget": requirement.budget,
        "currency": requirement.currency,

        "mandatory_constraints": (
            requirement.mandatory_constraints
        ),

        "preferences": requirement.preferences,
    }
