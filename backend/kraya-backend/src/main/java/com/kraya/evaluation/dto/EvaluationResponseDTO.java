
package com.kraya.evaluation.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
public class EvaluationResponseDTO {

    @JsonProperty("supplier_id")
    private String supplierId;

    @JsonProperty("quote_id")
    private String quoteId;

    @JsonProperty("final_score")
    private Double finalScore;

    @JsonProperty("baseline_score")
    private Double baselineScore;

    @JsonProperty("shap_breakdown")
    private ShapBreakdown shapBreakdown;

    @Data
    public static class ShapBreakdown {

        @JsonProperty("base_value")
        private Double baseValue;

        @JsonProperty("top_positive_drivers")
        private List<FeatureAttributionDTO> topPositiveDrivers;

        @JsonProperty("top_negative_drivers")
        private List<FeatureAttributionDTO> topNegativeDrivers;
    }
}
