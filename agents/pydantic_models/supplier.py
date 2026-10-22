from pydantic import BaseModel, Field
from typing import Optional


class Supplier(BaseModel):
    supplier_id: int

    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    address: Optional[str] = None
    country: Optional[str] = None

    tax_id: Optional[str] = None

    rating: Optional[float] = Field(
        default=None,
        ge=0,
        le=5
    )

    is_verified: bool = False
    is_active: bool = True