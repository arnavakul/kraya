
package com.kraya.evaluation.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class EvaluationRequestDTO {

    @JsonProperty("price_variance_pct")
    private Double priceVariancePct;

    @JsonProperty("tco_markup_pct")
    private Double tcoMarkupPct;

    @JsonProperty("lead_time_days_delta")
    private Double leadTimeDaysDelta;

    @JsonProperty("historical_delay_avg_days")
    private Double historicalDelayAvgDays;

    @JsonProperty("historical_defect_rate")
    private Double historicalDefectRate;

    @JsonProperty("payment_terms_penalty")
    private Double paymentTermsPenalty;

    @JsonProperty("warranty_months")
    private Double warrantyMonths;

    @JsonProperty("category_experience_years")
    private Double categoryExperienceYears;

    @JsonProperty("extraction_completeness_pct")
    private Double extractionCompletenessPct;

    @JsonProperty("anomaly_lowball_flag")
    private Double anomalyLowballFlag;
}
