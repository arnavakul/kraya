from datetime import date, datetime
from tests.pydantic_models.requirement import Requirement
from tests.pydantic_models.procurementRequest import ProcurementRequest

requirement = Requirement(
    product_service="Laptop",
    quantity=20,
    specifications="Intel i7, 16GB RAM, 512GB SSD",
    delivery_location="Kolkata",
    delivery_deadline=date(2026, 9, 15),
    budget=2000000,
    mandatory_constraints=["3-year warranty"],
    preferences=["Dell or Lenovo"]
)

request = ProcurementRequest(
    request_id=1,
    requester_name="Arnav",
    department="Engineering",
    requirement=requirement,
    budget=2000000,
    currency="INR",
    deadline=date(2026, 9, 15),
    priority="high",
    status="draft",
    created_at=datetime.now()
)

print(request)
