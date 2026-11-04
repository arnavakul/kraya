package com.kraya.evaluation.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "shap_attributions")
public class ShapAttributionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "feature_name", nullable = false)
    private String featureName;

    @Column(name = "display_label", nullable = false)
    private String displayLabel;

    @Column(name = "feature_value", nullable = false)
    private String featureValue;

    @Column(name = "shap_value", nullable = false)
    private BigDecimal shapValue;

    @Column(name = "score_delta", nullable = false)
    private BigDecimal scoreDelta;

    @Column(name = "is_positive", nullable = false)
    private Boolean isPositive;

    public Long getId() { return id; }
    public String getFeatureName() { return featureName; }
    public void setFeatureName(String featureName) { this.featureName = featureName; }
    public String getDisplayLabel() { return displayLabel; }
    public void setDisplayLabel(String displayLabel) { this.displayLabel = displayLabel; }
    public String getFeatureValue() { return featureValue; }
    public void setFeatureValue(String featureValue) { this.featureValue = featureValue; }
    public BigDecimal getShapValue() { return shapValue; }
    public void setShapValue(BigDecimal shapValue) { this.shapValue = shapValue; }
    public BigDecimal getScoreDelta() { return scoreDelta; }
    public void setScoreDelta(BigDecimal scoreDelta) { this.scoreDelta = scoreDelta; }
    public Boolean getIsPositive() { return isPositive; }
    public void setIsPositive(Boolean isPositive) { this.isPositive = isPositive; }
}
