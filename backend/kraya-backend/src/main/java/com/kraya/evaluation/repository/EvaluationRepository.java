
package com.kraya.evaluation.repository;

import com.kraya.evaluation.entity.EvaluationRecord;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface EvaluationRepository
        extends JpaRepository<EvaluationRecord, UUID> {

    List<EvaluationRecord> findBySupplierIdOrderByCreatedAtDesc(
            UUID supplierId);

    List<EvaluationRecord> findByQuoteIdOrderByCreatedAtDesc(
            UUID quoteId);
}
