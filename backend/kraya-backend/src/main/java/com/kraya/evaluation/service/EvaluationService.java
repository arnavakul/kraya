
package com.kraya.evaluation.service;

import com.kraya.evaluation.client.EvaluationAgentClient;
import com.kraya.evaluation.dto.EvaluationRequestDTO;
import com.kraya.evaluation.dto.EvaluationResponseDTO;
import com.kraya.evaluation.entity.EvaluationRecord;
import com.kraya.evaluation.repository.EvaluationRepository;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class EvaluationService {

    private final EvaluationAgentClient evaluationAgentClient;
    private final EvaluationRepository evaluationRepository;

    public EvaluationService(
            EvaluationAgentClient evaluationAgentClient,
            EvaluationRepository evaluationRepository) {
        this.evaluationAgentClient = evaluationAgentClient;
        this.evaluationRepository = evaluationRepository;
    }

    @Transactional
    public EvaluationResponseDTO evaluate(
            UUID supplierId,
            UUID quoteId,
            EvaluationRequestDTO request) {

        // 1. Call Python ML evaluation agent
        EvaluationResponseDTO response =
                evaluationAgentClient.evaluate(
                        supplierId.toString(),
                        quoteId.toString(),
                        request
                );

        // 2. Create database entity
        EvaluationRecord record = new EvaluationRecord();
        record.setSupplierId(supplierId);
        record.setQuoteId(quoteId);
        record.setCompositeScore(response.getFinalScore());
        record.setBaselineScore(response.getBaselineScore());

        // 3. Save evaluation result
        evaluationRepository.save(record);

        // 4. Return complete ML response
        return response;
    }
}
