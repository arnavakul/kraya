
from schemas.quotation import Quotation, DeliveryTimeUnit
from schemas.evaluation import ConstraintStatus


class ScoringEngine:
    """Calculates deterministic supplier scores out of 100."""

    WEIGHTS = {
        "price": 40,
        "delivery": 25,
        "warranty": 20,
        "payment_terms": 10,
        "validity": 5,
    }

    def evaluate(
        self,
        quotations: list[Quotation],
        constraint_results: dict[str, dict[str, ConstraintStatus]],
    ) -> list[dict]:

        if not quotations:
            return []

        currencies = {q.currency for q in quotations}

        if len(currencies) > 1:
            raise ValueError(
                "Cannot compare quotations with different currencies."
            )

        prices = [
            q.grand_total for q in quotations
            if q.grand_total is not None and q.grand_total > 0
        ]

        # Compare delivery only when suppliers use calendar days.
        deliveries = [
            q.delivery_time_days
            for q in quotations
            if q.delivery_time_days is not None
            and q.delivery_time_days > 0
            and q.delivery_time_unit == DeliveryTimeUnit.CALENDAR_DAYS
        ]

        warranties = [
            self._warranty_years(q.warranty_period)
            for q in quotations
        ]
        warranties = [w for w in warranties if w is not None]

        validities = [
            (q.valid_until - q.issue_date).days
            for q in quotations
            if q.issue_date and q.valid_until
        ]

        results = []

        for quotation in quotations:
            name = quotation.supplier_name or "Unknown Supplier"

            scores = {}
            availability = {}

            # 1. Price
            if quotation.grand_total and prices:
                scores["price"] = (
                    min(prices) / quotation.grand_total * 100
                )
                availability["price"] = True
            else:
                scores["price"] = 0.0
                availability["price"] = False

            # 2. Delivery: calendar days only
            if (
                quotation.delivery_time_days is not None
                and quotation.delivery_time_days > 0
                and quotation.delivery_time_unit == DeliveryTimeUnit.CALENDAR_DAYS
                and deliveries
            ):
                scores["delivery"] = (
                    min(deliveries) / quotation.delivery_time_days * 100
                )
                availability["delivery"] = True
            else:
                scores["delivery"] = 0.0
                availability["delivery"] = False

            # 3. Warranty
            warranty = self._warranty_years(
                quotation.warranty_period
            )

            if warranty is not None and warranties:
                scores["warranty"] = (
                    warranty / max(warranties) * 100
                )
                availability["warranty"] = True
            else:
                scores["warranty"] = 0.0
                availability["warranty"] = False

            # 4. Payment terms
            if quotation.payment_terms:
                scores["payment_terms"] = self._payment_score(
                    quotation.payment_terms
                )
                availability["payment_terms"] = True
            else:
                scores["payment_terms"] = 0.0
                availability["payment_terms"] = False

            # 5. Quotation validity
            if (
                quotation.issue_date
                and quotation.valid_until
                and validities
            ):
                validity = (
                    quotation.valid_until - quotation.issue_date
                ).days

                scores["validity"] = (
                    validity / max(validities) * 100
                    if max(validities) > 0 else 0.0
                )
                availability["validity"] = True
            else:
                scores["validity"] = 0.0
                availability["validity"] = False

            # Calculate weighted score.
            weighted_score = sum(
                float(scores[criterion]) * float(weight) / 100
                for criterion, weight in self.WEIGHTS.items()
            )

            weighted_score = round(weighted_score, 2)

            constraints = constraint_results.get(name, {})

            has_failed_constraint = any(
                status == ConstraintStatus.FAIL
                for status in constraints.values()
            )

            has_unknown_constraint = any(
                status == ConstraintStatus.UNKNOWN
                for status in constraints.values()
            )

            eligible = (
                bool(constraints)
                and not has_failed_constraint
                and not has_unknown_constraint
            )

            if has_failed_constraint:
                evaluation_status = "rejected"
            elif has_unknown_constraint or not constraints:
                evaluation_status = "pending_verification"
            else:
                evaluation_status = "eligible"

            results.append({
                "supplier_name": name,
                "criterion_scores": {
                    key: round(value, 2)
                    for key, value in scores.items()
                },
                "criterion_availability": availability,
                "weighted_score": round(weighted_score, 2),
                "mandatory_constraints": constraints,
                "eligible": eligible,
                "evaluation_status": evaluation_status,
            })

        # Only fully eligible suppliers receive a ranking.
        eligible_results = sorted(
            [r for r in results if r["eligible"]],
            key=lambda r: r["weighted_score"],
            reverse=True,
        )

        for rank, result in enumerate(eligible_results, start=1):
            result["ranking"] = rank

        for result in results:
            result.setdefault("ranking", None)

        return results

    @staticmethod
    def _warranty_years(value: str | None) -> float | None:
        if not value:
            return None

        import re

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*(year|yr|month)",
            value.lower(),
        )

        if not match:
            return None

        number = float(match.group(1))

        return number / 12 if match.group(2) == "month" else number

    @staticmethod
    def _payment_score(value: str | None) -> float:
        if not value:
            return 0.0

        terms = value.lower()

        if "100% advance" in terms or "full advance" in terms:
            return 20.0

        if "advance" in terms and (
            "delivery" in terms or "installation" in terms
        ):
            return 70.0

        if "after delivery" in terms or "after installation" in terms:
            return 100.0

        return 50.0
