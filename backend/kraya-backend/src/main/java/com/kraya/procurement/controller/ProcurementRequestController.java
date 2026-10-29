package com.kraya.procurement.controller;

import com.kraya.audit.dto.AuditEventResponse;
import com.kraya.common.api.PageResponse;
import com.kraya.procurement.dto.ProcurementRequestResponse;
import com.kraya.procurement.dto.ProcurementRequestSummary;
import com.kraya.procurement.dto.SaveProcurementRequest;
import com.kraya.procurement.dto.TransitionRequest;
import com.kraya.procurement.entity.RequestStatus;
import com.kraya.procurement.service.ProcurementRequestService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/requests")
public class ProcurementRequestController {

    private final ProcurementRequestService service;

    public ProcurementRequestController(ProcurementRequestService service) {
        this.service = service;
    }

    @GetMapping
    public PageResponse<ProcurementRequestSummary> list(
            @RequestParam(required = false) RequestStatus status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        return service.list(status, Math.max(page, 0), Math.min(Math.max(size, 1), 100));
    }

    @PostMapping
    public ResponseEntity<ProcurementRequestResponse> create(@Valid @RequestBody SaveProcurementRequest body) {
        ProcurementRequestResponse created = service.create(body);
        return ResponseEntity.created(URI.create("/api/v1/requests/" + created.id())).body(created);
    }

    @GetMapping("/{id}")
    public ProcurementRequestResponse get(@PathVariable UUID id) {
        return service.get(id);
    }

    @PutMapping("/{id}")
    public ProcurementRequestResponse update(@PathVariable UUID id, @Valid @RequestBody SaveProcurementRequest body) {
        return service.update(id, body);
    }

    @PostMapping("/{id}/submit")
    public ProcurementRequestResponse submit(@PathVariable UUID id) {
        return service.transition(id, RequestStatus.SUBMITTED, null);
    }

    @PostMapping("/{id}/transitions")
    public ProcurementRequestResponse transition(@PathVariable UUID id, @Valid @RequestBody TransitionRequest body) {
        return service.transition(id, body.to(), body.reason());
    }

    @GetMapping("/{id}/audit")
    public List<AuditEventResponse> audit(@PathVariable UUID id) {
        return service.history(id);
    }
}