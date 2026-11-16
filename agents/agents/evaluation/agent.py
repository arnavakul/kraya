
from schemas.quotation import Quotation
from schemas.evaluation import (
    EvaluationResult,
    SupplierEvaluation,
)

from agents.evaluation.constraint_checker import ConstraintChecker
from agents.evaluation.scoring_engine import ScoringEngine
from agents.evaluation.recommendation_explainer import (
    RecommendationExplainer,
)
from agents.evaluation.feature_builder import EvaluationFeatureBuilder
from agents.evaluation.ml_client import MLEvaluationClient
from schemas.evaluation import MLEvaluationStatus
from repositories.evaluation_repository import EvaluationRepository

class EvaluationAgent:

    def __init__(
        self,
        ml_client: MLEvaluationClient | None = None,
        evaluation_repository: EvaluationRepository | None = None,
    ):
        self.constraint_checker = ConstraintChecker()
        self.scoring_engine = ScoringEngine()
        self.explainer = RecommendationExplainer()

        self.feature_builder = EvaluationFeatureBuilder()
        self.ml_client = ml_client or MLEvaluationClient()

        self.evaluation_repository = (
            evaluation_repository or EvaluationRepository()
        )

    def evaluate_suppliers(
        self,
        quotations: list[Quotation],
        max_delivery_days: int = 20,
        min_warranty_years: int = 2,
        min_validity_days: int = 15,
        required_specs: list[str] | None = None,
    ) -> EvaluationResult:

        if not quotations:
            raise ValueError("At least one quotation is required.")

        constraint_results = {}

        # 1. Check mandatory constraints.
        for quotation in quotations:
            name = quotation.supplier_name or "Unknown Supplier"

            constraint_results[name] = self.constraint_checker.check(
                quotation=quotation,
                max_delivery_days=max_delivery_days,
                min_warranty_years=min_warranty_years,
                min_validity_days=min_validity_days,
                required_specs=required_specs,
            )

        # 2. Calculate deterministic scores.
        scores = self.scoring_engine.evaluate(
            quotations=quotations,
            constraint_results=constraint_results,
        )

        # 3. Prepare data for the recommendation explainer.
        evaluation_data = {
            "suppliers": scores,
            "weights": self.scoring_engine.WEIGHTS,
        }

        # 4. Generate evidence-based explanations.
        explanation = self.explainer.explain(evaluation_data)

        # 5. Build structured output.
        evaluations = []

        for score in scores:
            name = score["supplier_name"]

            evaluations.append(
                SupplierEvaluation(
                    supplier_name=name,
                    mandatory_constraints=score["mandatory_constraints"],
                    eligible=score["eligible"],
                    criterion_scores=score["criterion_scores"],
                    criterion_availability=score.get(
                        "criterion_availability", {}
                    ),
                    weighted_score=score["weighted_score"],
                    ranking=score["ranking"],
                    strengths=explanation["supplier_strengths"].get(
                        name, []
                    ),
                    weaknesses=explanation["supplier_weaknesses"].get(
                        name, []
                    ),
                    trade_offs=explanation["trade_offs"].get(
                        name, []
                    ),
                    evaluation_status=score["evaluation_status"],
                )
            )

        # Only the deterministic engine decides eligibility and selection.
        eligible = [
            item for item in evaluations
            if item.eligible
        ]

        recommended_supplier = (
            eligible[0].supplier_name if eligible else None
        )

        return EvaluationResult(
            evaluations=evaluations,
            recommended_supplier=recommended_supplier,
            recommendation_summary=explanation["recommendation_summary"],
            recommendation_reasoning=explanation["recommendation_reasoning"],
        )
        
    async def evaluate_suppliers_with_ml(
        self,
        quotations: list[Quotation],
        max_delivery_days: int = 20,
        min_warranty_years: int = 2,
        min_validity_days: int = 15,
        required_specs: list[str] | None = None,
        ml_context: dict[str, dict] | None = None,
    ) -> EvaluationResult:
        """
        Run deterministic evaluation first, then add ML results
        only when all required features and identifiers are available.

        ml_context is keyed by supplier name. It may contain:
        supplier_id, quote_id, market_benchmark_price,
        shipping_and_hidden_costs, historical_delay_avg_days,
        historical_defect_rate, payment_terms_penalty,
        category_experience_years and anomaly_lowball_flag.
        """

        # Preserve the existing deterministic evaluation.
        result = self.evaluate_suppliers(
            quotations=quotations,
            max_delivery_days=max_delivery_days,
            min_warranty_years=min_warranty_years,
            min_validity_days=min_validity_days,
            required_specs=required_specs,
        )

        ml_context = ml_context or {}

        updated_evaluations = []

        for evaluation in result.evaluations:
            quotation = next(
                (
                    item for item in quotations
                    if (item.supplier_name or "Unknown Supplier")
                    == evaluation.supplier_name
                ),
                None,
            )

            if quotation is None:
                updated_evaluations.append(evaluation)
                continue

            context = ml_context.get(evaluation.supplier_name, {})

            # Build features only from supplied, verified information.
            build_result = self.feature_builder.build(
                quotation=quotation,
                target_lead_time_days=max_delivery_days,
                market_benchmark_price=context.get(
                    "market_benchmark_price"
                ),
                shipping_and_hidden_costs=context.get(
                    "shipping_and_hidden_costs"
                ),
                historical_delay_avg_days=context.get(
                    "historical_delay_avg_days"
                ),
                historical_defect_rate=context.get(
                    "historical_defect_rate"
                ),
                payment_terms_penalty=context.get(
                    "payment_terms_penalty"
                ),
                category_experience_years=context.get(
                    "category_experience_years"
                ),
                anomaly_lowball_flag=context.get(
                    "anomaly_lowball_flag"
                ),
            )

            # Missing features mean no ML request.
            if not build_result.ready_for_ml:
                updated_evaluations.append(
                    evaluation.model_copy(
                        update={
                            "ml_status": (
                                MLEvaluationStatus.SKIPPED_MISSING_FEATURES
                            ),
                            "ml_missing_features": (
                                build_result.missing_features
                            ),
                            "ml_reasons": build_result.reasons,
                        }
                    )
                )
                continue

            supplier_id = context.get("supplier_id")
            quote_id = context.get("quote_id")

            if not supplier_id or not quote_id:
                updated_evaluations.append(
                    evaluation.model_copy(
                        update={
                            "ml_status": (
                                MLEvaluationStatus.SKIPPED_MISSING_FEATURES
                            ),
                            "ml_reasons": [
                                "Actual supplier_id and quote_id are required "
                                "to request an ML evaluation."
                            ],
                        }
                    )
                )
                continue

            # Check API availability before requesting inference.
            if not await self.ml_client.health_check():
                updated_evaluations.append(
                    evaluation.model_copy(
                        update={
                            "ml_status": (
                                MLEvaluationStatus.SKIPPED_API_UNAVAILABLE
                            ),
                            "ml_reasons": [
                                "ML Evaluation API is unavailable."
                            ],
                        }
                    )
                )
                continue

            try:
                ml_result = await self.ml_client.evaluate_supplier(
                    supplier_id=str(supplier_id),
                    quote_id=str(quote_id),
                    features=build_result.features,
                )

                updated_evaluations.append(
                    evaluation.model_copy(
                        update={
                            "ml_status": MLEvaluationStatus.COMPLETED,
                            "ml_score": ml_result.final_score,
                            "ml_baseline_score": ml_result.baseline_score,
                            "ml_shap_breakdown": (
                                ml_result.shap_breakdown
                            ),
                            "ml_missing_features": [],
                            "ml_reasons": [],
                        }
                    )
                )

            except RuntimeError as exc:
                updated_evaluations.append(
                    evaluation.model_copy(
                        update={
                            "ml_status": MLEvaluationStatus.FAILED,
                            "ml_reasons": [str(exc)],
                        }
                    )
                )

        result.evaluations = updated_evaluations

        # Deterministic recommendation remains untouched.
        return result


    async def evaluate_and_save(
        self,
        quotations: list[Quotation],
        evaluation_context: dict[str, dict],
        use_ml: bool = True,
        max_delivery_days: int = 20,
        min_warranty_years: int = 2,
        min_validity_days: int = 15,
        required_specs: list[str] | None = None,
    ) -> EvaluationResult:
        """
        Evaluate quotations and save deterministic scores
        to Supabase using actual supplier and quote IDs.
        """

        if use_ml:
            result = await self.evaluate_suppliers_with_ml(
                quotations=quotations,
                max_delivery_days=max_delivery_days,
                min_warranty_years=min_warranty_years,
                min_validity_days=min_validity_days,
                required_specs=required_specs,
                ml_context=evaluation_context,
            )
        else:
            result = self.evaluate_suppliers(
                quotations=quotations,
                max_delivery_days=max_delivery_days,
                min_warranty_years=min_warranty_years,
                min_validity_days=min_validity_days,
                required_specs=required_specs,
            )

        for evaluation in result.evaluations:
            context = evaluation_context.get(
                evaluation.supplier_name, {}
            )

            supplier_id = context.get("supplier_id")
            quote_id = context.get("quote_id")

            if not supplier_id or not quote_id:
                raise ValueError(
                    f"Missing supplier_id or quote_id for "
                    f"{evaluation.supplier_name}. Evaluation was "
                    "not saved."
                )

            self.evaluation_repository.save_evaluation(
                supplier_id=str(supplier_id),
                quote_id=str(quote_id),
                composite_score=evaluation.weighted_score,
                baseline_score=None,
            )

        return result
