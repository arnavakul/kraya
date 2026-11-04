package com.kraya.evaluation.client;

import com.kraya.evaluation.dto.EvaluationResponseDTO;
import com.kraya.evaluation.dto.FeatureVectorDTO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;

@FeignClient(name = "evaluation-agent", url = "${kraya.agents.evaluation-url:http://localhost:8000}")
public interface AgentEvaluationClient {

    @PostMapping("/evaluations/score-and-explain")
    EvaluationResponseDTO scoreAndExplain(
        @RequestParam("supplier_id") String supplierId,
        @RequestParam("quote_id") String quoteId,
        @RequestBody FeatureVectorDTO featureVector
    );
}