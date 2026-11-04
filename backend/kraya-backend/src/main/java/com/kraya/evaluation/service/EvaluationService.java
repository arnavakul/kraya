package com.kraya.evaluation.service;

import com.kraya.evaluation.client.AgentEvaluationClient;
import com.kraya.evaluation.dto.EvaluationResponseDTO;
import com.kraya.evaluation.dto.FeatureVectorDTO;
import com.kraya.evaluation.entity.EvaluationRecordEntity;
import com.kraya.evaluation.entity.ShapAttributionEntity;
import com.kraya.evaluation.repository.EvaluationRecordRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Service
public class EvaluationService {

    private final AgentEvaluationClient agentClient;
    private final EvaluationRecordRepository repository;

    public EvaluationService(AgentEvaluationClient agentClient, EvaluationRecordRepository repository) {
        this.agentClient = agentClient;
        this.repository = repository;
    }

    @Transactional
    public EvaluationResponseDTO evaluateQuote(String supplierId, String quoteId, FeatureVectorDTO features) {
        // 1. Call Python FastAPI microservice via Feign
        EvaluationResponseDTO response = agentClient.scoreAndExplain(supplierId, quoteId, features);

        // 2. Map response DTO to JPA Entity for PostgreSQL persistence
        EvaluationRecordEntity record = new EvaluationRecordEntity();
        record.setSupplierId(response.supplierId());
        record.setQuoteId(response.quoteId());
        record.setFinalScore(BigDecimal.valueOf(response.finalScore()));
        record.setBaselineScore(BigDecimal.valueOf(response.baselineScore()));

        List<ShapAttributionEntity> attributions = new ArrayList<>();
        
        // Map positive drivers
        if (response.shapBreakdown() != null && response.shapBreakdown().topPositiveDrivers() != null) {
            for (EvaluationResponseDTO.FeatureImpactDTO impact : response.shapBreakdown().topPositiveDrivers()) {
                attributions.add(mapToEntity(impact, true));
            }
        }

        // Map negative drivers
        if (response.shapBreakdown() != null && response.shapBreakdown().topNegativeDrivers() != null) {
            for (EvaluationResponseDTO.FeatureImpactDTO impact : response.shapBreakdown().topNegativeDrivers()) {
                attributions.add(mapToEntity(impact, false));
            }
        }

        record.setAttributions(attributions);
        repository.save(record);

        return response;
    }

    private ShapAttributionEntity mapToEntity(EvaluationResponseDTO.FeatureImpactDTO impact, boolean isPositive) {
        ShapAttributionEntity entity = new ShapAttributionEntity();
        entity.setFeatureName(impact.featureName());
        entity.setDisplayLabel(impact.displayLabel());
        entity.setFeatureValue(impact.featureValue());
        entity.setShapValue(BigDecimal.valueOf(impact.shapValue()));
        entity.setScoreDelta(BigDecimal.valueOf(impact.scoreDelta()));
        entity.setIsPositive(isPositive);
        return entity;
    }
}