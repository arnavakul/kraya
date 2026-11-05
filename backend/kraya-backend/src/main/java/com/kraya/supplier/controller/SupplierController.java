package com.kraya.supplier.controller;

import com.kraya.common.api.PageResponse;
import com.kraya.supplier.dto.SaveSupplierRequest;
import com.kraya.supplier.dto.SupplierResponse;
import com.kraya.supplier.dto.SupplierStatusRequest;
import com.kraya.supplier.dto.SupplierSummary;
import com.kraya.supplier.entity.SupplierStatus;
import com.kraya.supplier.service.SupplierService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/suppliers")
public class SupplierController {

    private final SupplierService service;

    public SupplierController(SupplierService service) {
        this.service = service;
    }

    @GetMapping
    public PageResponse<SupplierSummary> list(
            @RequestParam(required = false) SupplierStatus status,
            @RequestParam(required = false) String q,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        return service.list(status, q, Math.max(page, 0), Math.min(Math.max(size, 1), 100));
    }

    @PostMapping
    public ResponseEntity<SupplierResponse> create(@Valid @RequestBody SaveSupplierRequest body) {
        SupplierResponse created = service.create(body);
        return ResponseEntity.created(URI.create("/api/v1/suppliers/" + created.id())).body(created);
    }

    @GetMapping("/{id}")
    public SupplierResponse get(@PathVariable UUID id) {
        return service.get(id);
    }

    @PutMapping("/{id}")
    public SupplierResponse update(@PathVariable UUID id, @Valid @RequestBody SaveSupplierRequest body) {
        return service.update(id, body);
    }

    @PostMapping("/{id}/status")
    public SupplierResponse changeStatus(@PathVariable UUID id, @Valid @RequestBody SupplierStatusRequest body) {
        return service.changeStatus(id, body.status(), body.reason());
    }
}
