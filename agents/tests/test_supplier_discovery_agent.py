
from agents.supplier_discovery.agent import (
    run_supplier_discovery_agent
)


def test_supplier_discovery():

    requirement = {
        "product_service": "demoCommercial",
        "country_code": "IN"
    }

    result = run_supplier_discovery_agent(requirement)

    assert result.status == "completed"
    assert result.total_candidates >= 1

    supplier = result.suppliers[0]

    assert supplier.supplier.name == "Demo1"
    assert supplier.matching.overall_status == "matched"
    assert len(supplier.verification_evidence) > 0


def test_supplier_discovery_no_candidates():

    requirement = {
        "product_service": "nonexistent_category_xyz"
    }

    result = run_supplier_discovery_agent(requirement)

    assert result.status == "no_candidates"
    assert result.total_candidates == 0


def test_supplier_discovery_missing_requirement():

    result = run_supplier_discovery_agent({})

    assert result.status == "failed"
    assert result.total_candidates == 0
