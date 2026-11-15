
from datetime import datetime, timezone

from pydantic_models.verification_evidence import VerificationEvidence


def verify_supplier(supplier):

    evidence = []
    now = datetime.now(timezone.utc)

    def add_evidence(
        field,
        value,
        status,
        notes=None
    ):
        evidence.append(
            VerificationEvidence(
                field=field,
                value=str(value) if value is not None else None,
                source="supplier_database",
                verification_status=status,
                checked_at=now,
                notes=notes
            )
        )

    # 1. Supplier account status
    if supplier.status == "ACTIVE":
        add_evidence(
            "supplier_status",
            supplier.status,
            "verified",
            "Supplier is marked ACTIVE in the database."
        )
    else:
        add_evidence(
            "supplier_status",
            supplier.status,
            "inconsistent",
            "Supplier is not marked ACTIVE."
        )

    # 2. Organization type
    if supplier.organization_type == "SUPPLIER":
        add_evidence(
            "organization_type",
            supplier.organization_type,
            "verified",
            "Organization is classified as a supplier."
        )
    else:
        add_evidence(
            "organization_type",
            supplier.organization_type,
            "inconsistent",
            "Organization is not classified as SUPPLIER."
        )

    # 3. Organization verification flag
    if supplier.organization_verified is True:
        add_evidence(
            "organization_verified",
            True,
            "verified",
            "Organization verification flag is true in the database."
        )
    else:
        add_evidence(
            "organization_verified",
            supplier.organization_verified,
            "unverified",
            "Organization verification is not confirmed."
        )

    # 4. Tax ID
    if supplier.tax_id and supplier.tax_id.strip():
        add_evidence(
            "tax_id",
            "Present",
            "unverified",
            "Tax ID exists, but its validity has not been independently checked."
        )
    else:
        add_evidence(
            "tax_id",
            None,
            "not_available",
            "Tax ID is missing."
        )

    # 5. Contact email
    if supplier.contact_email:
        add_evidence(
            "contact_email",
            supplier.contact_email,
            "unverified",
            "Email is present but has not been independently validated."
        )
    else:
        add_evidence(
            "contact_email",
            None,
            "not_available",
            "Contact email is missing."
        )

    # 6. Contact phone
    if supplier.contact_phone:
        add_evidence(
            "contact_phone",
            supplier.contact_phone,
            "unverified",
            "Phone number is present but has not been validated."
        )
    else:
        add_evidence(
            "contact_phone",
            None,
            "not_available",
            "Contact phone is missing."
        )

    # 7. Website
    if supplier.website_url:
        add_evidence(
            "website_url",
            supplier.website_url,
            "unverified",
            "Website URL is recorded but has not been checked."
        )
    else:
        add_evidence(
            "website_url",
            None,
            "not_available",
            "Website URL is missing."
        )

    # 8. Categories
    if supplier.categories:
        add_evidence(
            "categories",
            ", ".join(supplier.categories),
            "unverified",
            "Categories are recorded in the supplier database."
        )
    else:
        add_evidence(
            "categories",
            None,
            "not_available",
            "No supplier categories are recorded."
        )

    return evidence
