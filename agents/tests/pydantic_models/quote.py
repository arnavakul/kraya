from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class QuoteLineItem(BaseModel):
    product_service: str
    quantity: float = Field(gt=0)

    unit_price: float = Field(ge=0)

    tax: float = Field(default=0, ge=0)
    discount: float = Field(default=0, ge=0)

    total_price: float = Field(ge=0)


class Quote(BaseModel):
    quote_id: int

    supplier_id: int
    currency: str

    line_items: List[QuoteLineItem]

    subtotal: float = Field(ge=0)
    taxes: float = Field(default=0, ge=0)
    shipping: float = Field(default=0, ge=0)

    total_price: float = Field(ge=0)

    delivery_days: Optional[int] = Field(default=None, ge=0)

    payment_terms: Optional[str] = None
    warranty: Optional[str] = None

    validity: Optional[date] = None

    source_document: Optional[str] = None