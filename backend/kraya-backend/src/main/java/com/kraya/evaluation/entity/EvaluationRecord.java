
package com.kraya.evaluation.entity;

import jakarta.persistence.*;
import lombok.Data;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "evaluation_records")
@Data
public class EvaluationRecord {

    @Id
    private UUID id = UUID.randomUUID();

    @Column(name = "supplier_id", nullable = false)
    private UUID supplierId;

    @Column(name = "quote_id", nullable = false)
    private UUID quoteId;

    @Column(name = "composite_score", nullable = false)
    private Double compositeScore;

    @Column(name = "baseline_score")
    private Double baselineScore;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
    }
}
