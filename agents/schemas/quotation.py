
from datetime import date
from decimal import Decimal
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, AliasChoices

class ShippingStatus(str, Enum):
    AMOUNT = "amount"
    INCLUDED = "included"
    NOT_STATED = "not_stated"

class DeliveryTimeUnit(str, Enum):
    CALENDAR_DAYS = "calendar_days"
    WORKING_DAYS = "working_days"
    NOT_SPECIFIED = "not_specified"



from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, AliasChoices


class TaxComponent(BaseModel):
    """Represents an individual tax applied to a quotation."""

    name: str = Field(
        ...,
        validation_alias=AliasChoices(
            "name",
            "type",
            "tax_name"
        )
    )

    rate: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        validation_alias=AliasChoices(
            "rate",
            "tax_rate"
        )
    )

    amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices(
            "amount",
            "tax_amount"
        )
    )



class QuoteLineItem(BaseModel):
    """Represents one product or service in a supplier quotation."""

    product_name: str
    description: Optional[str] = None

    quantity: Decimal = Field(gt=0)
    unit: Optional[str] = None

    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_total: Optional[Decimal] = Field(default=None, ge=0)

    taxes: list[TaxComponent] = Field(default_factory=list)


class Quotation(BaseModel):
    """Standardized quotation structure for Kraya."""

    model_config = ConfigDict(extra="forbid")

    # Supplier information
    supplier_name: Optional[str] = None
    supplier_email: Optional[str] = None
    quotation_number: Optional[str] = None

    # Quotation dates
    issue_date: Optional[date] = None
    valid_until: Optional[date] = None

    # Currency
    currency: Optional[str] = None

    # Products and services
    line_items: list[QuoteLineItem] = Field(default_factory=list)

    # Financial information
    subtotal: Optional[Decimal] = Field(default=None, ge=0)
    taxes: list[TaxComponent] = Field(default_factory=list)
    shipping_cost: Optional[Decimal] = Field(default=None, ge=0)
    shipping_status: ShippingStatus = ShippingStatus.NOT_STATED
    discount: Optional[Decimal] = Field(default=None, ge=0)
    grand_total: Optional[Decimal] = Field(default=None, ge=0)

    # Delivery information
    delivery_time_days: Optional[int] = Field(default=None, ge=0)
    delivery_time_unit: DeliveryTimeUnit = DeliveryTimeUnit.NOT_SPECIFIED
    warranty_period: Optional[str] = None

    # Commercial terms
    payment_terms: Optional[str] = None
    additional_terms: Optional[str] = None


