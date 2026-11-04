package com.kraya.evaluation.repository;

import com.kraya.evaluation.entity.EvaluationRecordEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface EvaluationRecordRepository extends JpaRepository<EvaluationRecordEntity, String> {
    List<EvaluationRecordEntity> findByQuoteId(String quoteId);
    List<EvaluationRecordEntity> findBySupplierId(String supplierId);
}