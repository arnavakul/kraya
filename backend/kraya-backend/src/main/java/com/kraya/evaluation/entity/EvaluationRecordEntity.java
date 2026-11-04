package com.kraya.evaluation.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "evaluation_records")
public class EvaluationRecordEntity {

    @Id
    private String id;

    @Column(name = "supplier_id", nullable = false)
    private String supplierId;

    @Column(name = "quote_id", nullable = false)
    private String quoteId;

    @Column(name = "final_score", nullable = false)
    private BigDecimal finalScore;

    @Column(name = "baseline_score", nullable = false)
    private BigDecimal baselineScore;

    @Column(name = "evaluated_at")
    private OffsetDateTime evaluatedAt;

    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    @JoinColumn(name = "evaluation_id")
    private List<ShapAttributionEntity> attributions = new ArrayList<>();

    public EvaluationRecordEntity() {
        this.id = UUID.randomUUID().toString();
        this.evaluatedAt = OffsetDateTime.now();
    }

    public String getId() { return id; }
    public String getSupplierId() { return supplierId; }
    public void setSupplierId(String supplierId) { this.supplierId = supplierId; }
    public String getQuoteId() { return quoteId; }
    public void setQuoteId(String quoteId) { this.quoteId = quoteId; }
    public BigDecimal getFinalScore() { return finalScore; }
    public void setFinalScore(BigDecimal finalScore) { this.finalScore = finalScore; }
    public BigDecimal getBaselineScore() { return baselineScore; }
    public void setBaselineScore(BigDecimal baselineScore) { this.baselineScore = baselineScore; }
    public OffsetDateTime getEvaluatedAt() { return evaluatedAt; }
    public List<ShapAttributionEntity> getAttributions() { return attributions; }
    public void setAttributions(List<ShapAttributionEntity> attributions) { this.attributions = attributions; }
}