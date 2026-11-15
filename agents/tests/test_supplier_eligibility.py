
from tools.rfq.supplier_eligibility import (
    evaluate_supplier_eligibility
)


def test_matched_supplier_without_issues_is_eligible():

    assessment = {
        "matching": {
            "overall_status": "matched"
        },
        "verification_issues": []
    }

    result = evaluate_supplier_eligibility(assessment)

    assert result["eligible"] is True
    assert result["decision"] == "eligible"


def test_unmatched_supplier_is_excluded():

    assessment = {
        "matching": {
            "overall_status": "not_matched"
        },
        "verification_issues": []
    }

    result = evaluate_supplier_eligibility(assessment)

    assert result["eligible"] is False
    assert result["decision"] == "excluded"


def test_partially_matched_supplier_requires_review():

    assessment = {
        "matching": {
            "overall_status": "partially_matched"
        },
        "verification_issues": []
    }

    result = evaluate_supplier_eligibility(assessment)

    assert result["eligible"] is False
    assert result["decision"] == "manual_review"


def test_supplier_with_verification_issues_requires_review():

    assessment = {
        "matching": {
            "overall_status": "matched"
        },
        "verification_issues": [
            "Tax ID: not independently verified"
        ]
    }

    result = evaluate_supplier_eligibility(assessment)

    assert result["eligible"] is False
    assert result["decision"] == "manual_review"
