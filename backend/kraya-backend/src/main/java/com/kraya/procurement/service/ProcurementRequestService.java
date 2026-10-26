package com.kraya.procurement.service;


import com.kraya.audit.dto.AuditEventResponse;
import com.kraya.audit.service.AuditService;
import com.kraya.common.api.PageResponse;
import com.kraya.common.exception.ForbiddenException;
import com.kraya.common.exception.ResourceNotFoundException;
import com.kraya.common.security.CurrentUser;
import com.kraya.common.security.CurrentUserProvider;
import com.kraya.procurement.dto.ItemResponse;
import com.kraya.procurement.dto.ProcurementRequestResponse;
import com.kraya.procurement.dto.ProcurementRequestSummary;
import com.kraya.procurement.dto.SaveProcurementRequest;
import com.kraya.procurement.entity.ProcurementRequest;
import com.kraya.procurement.entity.RequestStatus;
import com.kraya.procurement.repository.ProcurementRequestRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class ProcurementRequestService {

    private static final String ENTITY_TYPE = "PROCUREMENT_REQUEST";

    private final ProcurementRequestRepository repository;
    private final AuditService auditService;
    private final CurrentUserProvider currentUserProvider;

    public ProcurementRequestService(
            ProcurementRequestRepository repository,
            AuditService auditService,
            CurrentUserProvider currentUserProvider
    ) {
       this.repository = repository;
       this.auditService = auditService;
       this.currentUserProvider = currentUserProvider;
    }

    @Transactional
    public ProcurementRequestResponse create(SaveProcurementRequest input) {
        CurrentUser user = manager();
        String reference = "PR-" + String.format("%05d", repository.nextReferenceNumber());

        ProcurementRequest request = ProcurementRequest.draft(user.organizationId(), user.userId(), reference);
        applyInput(request, input);
        ProcurementRequest saved = repository.save(request);

        auditService.record(user, "REQUEST_CREATED", ENTITY_TYPE, saved.getId(),
                null, saved.getStatus().name());
        return toResponse(saved);
    }

    @Transactional
    public ProcurementRequestResponse update(UUID id, SaveProcurementRequest input) {
        CurrentUser user = manager();
        ProcurementRequest request = load(id, user);

        applyInput(request, input);
        repository.saveAndFlush(request);

        auditService.record(user, "REQUEST_UPDATED", ENTITY_TYPE, request.getId(),
                request.getStatus().name(), request.getStatus().name());
        return toResponse(request);
    }

    @Transactional
    public ProcurementRequestResponse transition(UUID id, RequestStatus to, String reason) {
        CurrentUser user = manager();
        ProcurementRequest request = load(id, user);

        RequestStatus from = request.getStatus();
        request.transitionTo(to, reason);
        repository.saveAndFlush(request);

        auditService.record(user, "REQUEST_STATUS_CHANGED", ENTITY_TYPE, request.getId(),
                from.name(), to.name());
        return toResponse(request);
    }

    @Transactional(readOnly = true)
    public ProcurementRequestResponse get(UUID id) {
        return toResponse(load(id, currentUserProvider.require()));
    }

    @Transactional(readOnly = true)
    public PageResponse<ProcurementRequestSummary> list(RequestStatus status, int page, int size) {
        CurrentUser user = currentUserProvider.require();
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));

        Page<ProcurementRequest> result = status == null
                ? repository.findByOrganizationId(user.organizationId(), pageable)
                : repository.findByOrganizationIdAndStatus(user.organizationId(), status, pageable);

        return PageResponse.of(result.map(this::toSummary));
    }

    @Transactional(readOnly = true)
    public List<AuditEventResponse> history(UUID id) {
        CurrentUser user = currentUserProvider.require();
        load(id, user); // 404 unless the request belongs to the caller's organization
        return auditService.history(user.organizationId(), ENTITY_TYPE, id);
    }

    // ---------- helpers ----------

    private CurrentUser manager() {
        CurrentUser user = currentUserProvider.require();
        if (!user.canManageProcurement()) {
            throw new ForbiddenException("Your role cannot modify procurement requests");
        }
        return user;
    }

    private ProcurementRequest load(UUID id, CurrentUser user) {
        return repository.findByIdAndOrganizationId(id, user.organizationId())
                .orElseThrow(() -> new ResourceNotFoundException("Procurement request not found: " + id));
    }

    private void applyInput(ProcurementRequest request, SaveProcurementRequest in) {
        List<ProcurementRequest.ItemData> items = in.items().stream()
                .map(i -> new ProcurementRequest.ItemData(
                        i.name().trim(), blankToNull(i.description()), i.quantity(), i.unit().trim()))
                .toList();

        request.updateDetails(
                in.title().trim(),
                blankToNull(in.description()),
                blankToNull(in.category()),
                in.budgetAmount(),
                in.currencyCode() == null ? "INR" : in.currencyCode().toUpperCase(),
                in.neededBy(),
                blankToNull(in.deliveryLocation()),
                items);
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value.trim();
    }

    private ProcurementRequestSummary toSummary(ProcurementRequest r) {
        return new ProcurementRequestSummary(r.getId(), r.getReference(), r.getTitle(), r.getStatus(),
                r.getBudgetAmount(), r.getCurrencyCode(), r.getNeededBy(), r.getCreatedAt());
    }

    private ProcurementRequestResponse toResponse(ProcurementRequest r) {
        List<ItemResponse> items = r.getItems().stream()
                .map(i -> new ItemResponse(i.getId(), i.getLineNo(), i.getName(), i.getDescription(),
                        i.getQuantity(), i.getUnit()))
                .toList();

        return new ProcurementRequestResponse(
                r.getId(), r.getReference(), r.getTitle(), r.getDescription(), r.getCategory(),
                r.getBudgetAmount(), r.getCurrencyCode(), r.getNeededBy(), r.getDeliveryLocation(),
                r.getStatus(), r.getStatusReason(), r.getCreatedBy(), items,
                List.copyOf(r.getStatus().allowedNext()), r.getCreatedAt(), r.getUpdatedAt());
    }
}
