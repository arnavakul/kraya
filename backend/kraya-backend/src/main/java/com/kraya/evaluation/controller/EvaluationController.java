
package com.kraya.evaluation.controller;

import com.kraya.evaluation.dto.EvaluationRequestDTO;
import com.kraya.evaluation.dto.EvaluationResponseDTO;
import com.kraya.evaluation.service.EvaluationService;

import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/evaluations")
public class EvaluationController {

    private final EvaluationService evaluationService;

    public EvaluationController(EvaluationService evaluationService) {
        this.evaluationService = evaluationService;
    }

    @PostMapping("/score")
    public EvaluationResponseDTO evaluate(
            @RequestParam UUID supplierId,
            @RequestParam UUID quoteId,
            @RequestBody EvaluationRequestDTO request) {

        return evaluationService.evaluate(
                supplierId,
                quoteId,
                request
        );
    }
}
