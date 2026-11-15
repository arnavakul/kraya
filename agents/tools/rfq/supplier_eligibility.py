
def evaluate_supplier_eligibility(
    supplier_assessment: dict
) -> dict:

    matching = supplier_assessment.get("matching", {})
    verification_issues = supplier_assessment.get(
        "verification_issues", []
    )

    match_status = matching.get("overall_status")

    if match_status == "not_matched":
        return {
            "eligible": False,
            "decision": "excluded",
            "reason": "Supplier does not match the procurement requirements."
        }

    if match_status == "insufficient_data":
        return {
            "eligible": False,
            "decision": "manual_review",
            "reason": "Insufficient supplier matching information."
        }

    if match_status == "partially_matched":
        return {
            "eligible": False,
            "decision": "manual_review",
            "reason": "Some procurement requirements could not be verified."
        }

    if verification_issues:
        return {
            "eligible": False,
            "decision": "manual_review",
            "reason": "Supplier has unresolved verification issues."
        }

    if match_status == "matched":
        return {
            "eligible": True,
            "decision": "eligible",
            "reason": "Supplier matches the available procurement criteria."
        }

    return {
        "eligible": False,
        "decision": "manual_review",
        "reason": "Supplier eligibility could not be determined."
    }
