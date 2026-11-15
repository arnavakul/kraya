from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID


class SupplierCandidate(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    supplier_id: UUID
    organization_id: UUID

    name: str

    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    country_code: Optional[str] = None
    website_url: Optional[str] = None
    tax_id: Optional[str] = None

    payment_terms: Optional[str] = None
    notes: Optional[str] = None

    status: str

    categories: list[str] = Field(default_factory=list)

    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    organization_verified: Optional[bool] = None
