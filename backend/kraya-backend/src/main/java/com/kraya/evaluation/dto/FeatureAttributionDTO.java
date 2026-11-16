
package com.kraya.evaluation.dto;

import lombok.Data;

@Data
public class FeatureAttributionDTO {

    private String featureName;

    private String displayLabel;

    private String featureValue;

    private Double shapValue;

    private Double scoreDelta;
}
