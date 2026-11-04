package com.kraya.evaluation.controller;

import com.kraya.evaluation.dto.EvaluationResponseDTO;
import com.kraya.evaluation.dto.FeatureVectorDTO;
import com.kraya.evaluation.service.EvaluationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/evaluations")
public class EvaluationController {

    private final EvaluationService evaluationService;

    public EvaluationController(EvaluationService evaluationService) {
        this.evaluationService = evaluationService;
    }

    @PostMapping("/evaluate")
    public ResponseEntity<EvaluationResponseDTO> evaluateQuote(
            @RequestParam("supplierId") String supplierId,
            @RequestParam("quoteId") String quoteId,
            @RequestBody FeatureVectorDTO features) {
        EvaluationResponseDTO response = evaluationService.evaluateQuote(supplierId, quoteId, features);
        return ResponseEntity.ok(response);
    }
}