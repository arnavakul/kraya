package com.kraya.evaluation.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record FeatureVectorDTO(
    @JsonProperty("price_variance_pct") Double priceVariancePct,
    @JsonProperty("tco_markup_pct") Double tcoMarkupPct,
    @JsonProperty("lead_time_days_delta") Double leadTimeDaysDelta,
    @JsonProperty("historical_delay_avg_days") Double historicalDelayAvgDays,
    @JsonProperty("historical_defect_rate") Double historicalDefectRate,
    @JsonProperty("payment_terms_penalty") Double paymentTermsPenalty,
    @JsonProperty("warranty_months") Double warrantyMonths,
    @JsonProperty("category_experience_years") Double categoryExperienceYears,
    @JsonProperty("extraction_completeness_pct") Double extractionCompletenessPct,
    @JsonProperty("anomaly_lowball_flag") Double anomalyLowballFlag
) {}