
from dataclasses import dataclass
from decimal import Decimal
import math
import re
from typing import Any

from schemas.ml_evaluation import FeatureVector
from schemas.quotation import (
    DeliveryTimeUnit,
    Quotation,
)


@dataclass
class FeatureBuildResult:
    """Result of preparing one supplier's ML feature vector."""

    ready_for_ml: bool
    features: FeatureVector | None
    available_features: dict[str, float]
    missing_features: list[str]
    reasons: list[str]


class EvaluationFeatureBuilder:
    """
    Builds the 10 features expected by Kraya's trained ML model.

    Missing information is never replaced with fabricated defaults.
    ML inference is allowed only when every required feature is available.
    """

    REQUIRED_FEATURES = [
        "price_variance_pct",
        "tco_markup_pct",
        "lead_time_days_delta",
        "historical_delay_avg_days",
        "historical_defect_rate",
        "payment_terms_penalty",
        "warranty_months",
        "category_experience_years",
        "extraction_completeness_pct",
        "anomaly_lowball_flag",
    ]

    COMPLETENESS_FIELDS = [
        "supplier_name",
        "currency",
        "line_items",
        "subtotal",
        "grand_total",
        "delivery_time_days",
        "warranty_period",
        "payment_terms",
        "issue_date",
        "valid_until",
    ]

    def build(
        self,
        quotation: Quotation,
        target_lead_time_days: int | None = None,
        market_benchmark_price: Decimal | None = None,
        shipping_and_hidden_costs: Decimal | None = None,
        historical_delay_avg_days: float | None = None,
        historical_defect_rate: float | None = None,
        payment_terms_penalty: float | None = None,
        category_experience_years: float | None = None,
        anomaly_lowball_flag: float | None = None,
    ) -> FeatureBuildResult:
        """
        Build features from a quotation and independently verified context.

        Optional inputs must come from real procurement or supplier records.
        Do not pass zero merely because a value is unavailable.
        """

        values: dict[str, float] = {}
        reasons: list[str] = []

        # 1. Price variance requires an independent market benchmark.
        quoted_price = quotation.grand_total
        benchmark_price = (
            Decimal(str(market_benchmark_price))
            if market_benchmark_price is not None
            else None
        )

        if (
            quoted_price is not None
            and benchmark_price is not None
            and benchmark_price.is_finite()
            and benchmark_price > 0
        ):
            values["price_variance_pct"] = float(
                (quoted_price - benchmark_price)
                / benchmark_price
            )
        else:
            reasons.append(
                "Price variance requires a quotation total and "
                "an independent market benchmark."
            )

        # 2. TCO markup requires separately identified additional costs.
        # The caller must ensure these costs are not already included
        # in the quoted price.
        extra_costs = (
            Decimal(str(shipping_and_hidden_costs))
            if shipping_and_hidden_costs is not None
            else None
        )
        if (
            quoted_price is not None
            and quoted_price > 0
            and extra_costs is not None
            and extra_costs.is_finite()
        ):
            values["tco_markup_pct"] = float(
                extra_costs / quoted_price
            )
        else:
            reasons.append(
                "TCO markup requires separately verified additional "
                "costs and a positive quoted total."
            )

        # 3. Delivery delta is comparable only when both values use
        # calendar days, matching the procurement target.
        delivery_unit = quotation.delivery_time_unit

        if (
            quotation.delivery_time_days is not None
            and target_lead_time_days is not None
            and delivery_unit == DeliveryTimeUnit.CALENDAR_DAYS
        ):
            values["lead_time_days_delta"] = float(
                quotation.delivery_time_days - target_lead_time_days
            )
        else:
            reasons.append(
                "Delivery delta requires a calendar-day quotation "
                "and a known target lead time."
            )

        # 4. Historical supplier delivery performance.
        if (
            historical_delay_avg_days is not None
            and math.isfinite(historical_delay_avg_days)
            and historical_delay_avg_days >= 0
        ):
            values["historical_delay_avg_days"] = float(
                historical_delay_avg_days
            )
        else:
            reasons.append(
                "Historical average delivery delay is unavailable "
                "or invalid."
            )

        # 5. Historical supplier defect rate.
        if (
            historical_defect_rate is not None
            and math.isfinite(historical_defect_rate)
            and 0 <= historical_defect_rate <= 1
        ):
            values["historical_defect_rate"] = float(
                historical_defect_rate
            )
        else:
            reasons.append(
                "Historical supplier defect rate is unavailable "
                "or invalid."
            )

        # 6. Payment penalty must be calculated using an explicit,
        # approved procurement policy. We do not guess from free text.
        if (
            payment_terms_penalty is not None
            and math.isfinite(payment_terms_penalty)
            and payment_terms_penalty >= 0
        ):
            values["payment_terms_penalty"] = float(
                payment_terms_penalty
            )
        else:
            reasons.append(
                "Payment penalty requires a verified value from "
                "the procurement payment policy."
            )

        # 7. Convert warranty into months.
        warranty_months = self._parse_warranty_months(
            quotation.warranty_period
        )

        if warranty_months is not None:
            values["warranty_months"] = warranty_months
        else:
            reasons.append(
                "Warranty duration is missing or cannot be interpreted."
            )

        # 8. Category experience must come from supplier history.
        if (
            category_experience_years is not None
            and math.isfinite(category_experience_years)
            and category_experience_years >= 0
        ):
            values["category_experience_years"] = float(
                category_experience_years
            )
        else:
            reasons.append(
                "Supplier experience in this category is unavailable."
            )

        # 9. Extraction completeness is calculated from actual
        # extracted quotation fields.
        values["extraction_completeness_pct"] = (
            self._calculate_extraction_completeness(quotation)
        )

        # 10. Low-ball anomaly requires an independent benchmark.
        if anomaly_lowball_flag is not None:
            if anomaly_lowball_flag in (0, 1, 0.0, 1.0):
                values["anomaly_lowball_flag"] = float(
                    anomaly_lowball_flag
                )
            else:
                reasons.append(
                    "Low-ball anomaly flag must be either 0 or 1."
                )
        elif "price_variance_pct" in values:
            # Match the threshold in the existing feature pipeline.
            values["anomaly_lowball_flag"] = (
                1.0
                if values["price_variance_pct"] < -0.25
                else 0.0
            )
        else:
            reasons.append(
                "Low-ball anomaly detection requires a market benchmark."
            )

        missing_features = [
            feature
            for feature in self.REQUIRED_FEATURES
            if feature not in values
        ]

        # Never construct FeatureVector with its default values when
        # required evidence is missing.
        if missing_features:
            return FeatureBuildResult(
                ready_for_ml=False,
                features=None,
                available_features=values,
                missing_features=missing_features,
                reasons=reasons,
            )

        # All ten features are now available and validated.
        features = FeatureVector(
            price_variance_pct=values["price_variance_pct"],
            tco_markup_pct=values["tco_markup_pct"],
            lead_time_days_delta=values["lead_time_days_delta"],
            historical_delay_avg_days=values[
                "historical_delay_avg_days"
            ],
            historical_defect_rate=values[
                "historical_defect_rate"
            ],
            payment_terms_penalty=values[
                "payment_terms_penalty"
            ],
            warranty_months=values["warranty_months"],
            category_experience_years=values[
                "category_experience_years"
            ],
            extraction_completeness_pct=values[
                "extraction_completeness_pct"
            ],
            anomaly_lowball_flag=values[
                "anomaly_lowball_flag"
            ],
        )

        return FeatureBuildResult(
            ready_for_ml=True,
            features=features,
            available_features=values,
            missing_features=[],
            reasons=[],
        )

    @staticmethod
    def _parse_warranty_months(
        warranty_period: str | None,
    ) -> float | None:
        """Convert a warranty duration such as '2 years' into months."""

        if not warranty_period:
            return None

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*"
            r"(years?|yrs?|months?|mos?)\b",
            warranty_period.lower(),
        )

        if not match:
            return None

        duration = float(match.group(1))
        unit = match.group(2)

        if unit.startswith(("year", "yr")):
            duration *= 12

        if not math.isfinite(duration) or duration < 0:
            return None

        return duration

    def _calculate_extraction_completeness(
        self,
        quotation: Quotation,
    ) -> float:
        """Calculate the proportion of known quotation fields."""

        available_count = 0

        for field in self.COMPLETENESS_FIELDS:
            value: Any = getattr(quotation, field, None)

            if value is None:
                continue

            if isinstance(value, str) and not value.strip():
                continue

            if isinstance(value, list) and not value:
                continue

            available_count += 1

        return round(
            available_count / len(self.COMPLETENESS_FIELDS),
            4,
        )
