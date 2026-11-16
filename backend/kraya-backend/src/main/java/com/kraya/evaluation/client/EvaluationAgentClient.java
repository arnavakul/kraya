
package com.kraya.evaluation.client;

import com.kraya.evaluation.dto.EvaluationRequestDTO;
import com.kraya.evaluation.dto.EvaluationResponseDTO;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class EvaluationAgentClient {

    private final RestClient restClient;

    public EvaluationAgentClient(
            @Value("${kraya.agents.evaluation-url:http://localhost:8000}")
            String evaluationUrl) {

        this.restClient = RestClient.builder()
                .baseUrl(evaluationUrl)
                .build();
    }

    public EvaluationResponseDTO evaluate(
            String supplierId,
            String quoteId,
            EvaluationRequestDTO request) {

        return restClient.post()
                .uri(uriBuilder -> uriBuilder
                        .path("/evaluations/score-and-explain")
                        .queryParam("supplier_id", supplierId)
                        .queryParam("quote_id", quoteId)
                        .build())
                .body(request)
                .retrieve()
                .body(EvaluationResponseDTO.class);
    }
}
