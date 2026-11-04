package com.kraya.evaluation.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record EvaluationResponseDTO(
    @JsonProperty("supplier_id") String supplierId,
    @JsonProperty("quote_id") String quoteId,
    @JsonProperty("final_score") Double finalScore,
    @JsonProperty("baseline_score") Double baselineScore,
    @JsonProperty("shap_breakdown") ShapBreakdownDTO shapBreakdown
) {
    public record FeatureImpactDTO(
        @JsonProperty("feature_name") String featureName,
        @JsonProperty("display_label") String displayLabel,
        @JsonProperty("feature_value") String featureValue,
        @JsonProperty("shap_value") Double shapValue,
        @JsonProperty("score_delta") Double scoreDelta
    ) {}

    public record ShapBreakdownDTO(
        @JsonProperty("base_value") Double baseValue,
        @JsonProperty("top_positive_drivers") List<FeatureImpactDTO> topPositiveDrivers,
        @JsonProperty("top_negative_drivers") List<FeatureImpactDTO> topNegativeDrivers
    ) {}
}