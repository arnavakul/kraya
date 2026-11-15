
from orchestration.graph import procurement_graph


def test_real_procurement_workflow():

    user_request = """
    I need 20 laptops for my organization.
    Each laptop should have:
    - Intel Core i7 processor
    - 16GB RAM
    - 512GB SSD
    - 3-year warranty

    Delivery location: Kolkata
    Budget: 20,00,000 INR
    """

    initial_state = {
        "user_input": user_request,
        "requirement_draft": None,
        "errors": []
    }

    result = procurement_graph.invoke(initial_state)

    print("\n========== PROCUREMENT WORKFLOW RESULT ==========")

    print("\nWorkflow Status:")
    print(result.get("intake_status"))

    print("\nExtracted Requirement:")
    print(result.get("requirement"))

    print("\nClarification Questions:")
    print(result.get("clarification_questions"))

    print("\nSupplier Discovery Status:")
    print(result.get("discovery_status"))

    print("\nSupplier Candidates:")
    print(result.get("supplier_candidates"))

    print("\n==================================================")

    # Basic workflow assertions
    assert result.get("intake_status") in [
        "validated",
        "needs_clarification"
    ]

    if result.get("intake_status") == "validated":
        assert result.get("discovery_status") in [
            "completed",
            "no_candidates",
            "failed"
        ]
