package com.kraya.supplier.service;

import com.kraya.audit.service.AuditService;
import com.kraya.common.api.PageResponse;
import com.kraya.common.exception.ConflictException;
import com.kraya.common.exception.ForbiddenException;
import com.kraya.common.exception.ResourceNotFoundException;
import com.kraya.common.security.CurrentUser;
import com.kraya.common.security.CurrentUserProvider;
import com.kraya.supplier.dto.SaveSupplierRequest;
import com.kraya.supplier.dto.SupplierResponse;
import com.kraya.supplier.dto.SupplierSummary;
import com.kraya.supplier.entity.Supplier;
import com.kraya.supplier.entity.SupplierStatus;
import com.kraya.supplier.repository.SupplierRepository;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Collection;
import java.util.EnumSet;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

@Service
public class SupplierService {

    private static final String ENTITY_TYPE = "SUPPLIER";
    private static final String EMAIL_TAKEN = "A supplier with this email already exists";

    private final SupplierRepository repository;
    private final AuditService auditService;
    private final CurrentUserProvider currentUserProvider;

    public SupplierService(SupplierRepository repository, AuditService auditService,
                           CurrentUserProvider currentUserProvider) {
        this.repository = repository;
        this.auditService = auditService;
        this.currentUserProvider = currentUserProvider;
    }

    @Transactional
    public SupplierResponse create(SaveSupplierRequest input) {
        CurrentUser user = manager();
        Supplier.Details details = toDetails(input);

        if (repository.existsByOrganizationIdAndContactEmail(user.organizationId(), details.contactEmail())) {
            throw new ConflictException(EMAIL_TAKEN);
        }

        Supplier supplier = Supplier.create(user.organizationId(), user.userId());
        supplier.updateDetails(details);
        Supplier saved = saveOrConflict(supplier);

        auditService.record(user, "SUPPLIER_CREATED", ENTITY_TYPE, saved.getId(),
                null, saved.getStatus().name());
        return toResponse(saved);
    }

    @Transactional
    public SupplierResponse update(UUID id, SaveSupplierRequest input) {
        CurrentUser user = manager();
        Supplier supplier = load(id, user);
        Supplier.Details details = toDetails(input);

        boolean emailChanged = !details.contactEmail().equals(supplier.getContactEmail());
        if (emailChanged && repository.existsByOrganizationIdAndContactEmail(user.organizationId(), details.contactEmail())) {
            throw new ConflictException(EMAIL_TAKEN);
        }

        supplier.updateDetails(details);
        saveOrConflict(supplier);

        auditService.record(user, "SUPPLIER_UPDATED", ENTITY_TYPE, supplier.getId(),
                supplier.getStatus().name(), supplier.getStatus().name());
        return toResponse(supplier);
    }

    @Transactional
    public SupplierResponse changeStatus(UUID id, SupplierStatus to, String reason) {
        CurrentUser user = manager();
        Supplier supplier = load(id, user);

        SupplierStatus from = supplier.getStatus();
        supplier.changeStatus(to, reason);
        repository.saveAndFlush(supplier);

        auditService.record(user, "SUPPLIER_STATUS_CHANGED", ENTITY_TYPE, supplier.getId(),
                from.name(), to.name());
        return toResponse(supplier);
    }

    @Transactional(readOnly = true)
    public SupplierResponse get(UUID id) {
        return toResponse(load(id, currentUserProvider.require()));
    }

    @Transactional(readOnly = true)
    public PageResponse<SupplierSummary> list(SupplierStatus status, String q, int page, int size) {
        CurrentUser user = currentUserProvider.require();
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.ASC, "name"));

        Collection<SupplierStatus> statuses = status == null
                ? EnumSet.allOf(SupplierStatus.class)
                : EnumSet.of(status);
        String pattern = q == null || q.isBlank() ? "%" : "%" + q.trim().toLowerCase(Locale.ROOT) + "%";

        Page<Supplier> result = repository.search(user.organizationId(), statuses, pattern, pageable);
        return PageResponse.of(result.map(this::toSummary));
    }

    // ---------- helpers ----------

    private CurrentUser manager() {
        CurrentUser user = currentUserProvider.require();
        if (!user.canManageProcurement()) {
            throw new ForbiddenException("Your role cannot modify suppliers");
        }
        return user;
    }

    private Supplier load(UUID id, CurrentUser user) {
        return repository.findByIdAndOrganizationId(id, user.organizationId())
                .orElseThrow(() -> new ResourceNotFoundException("Supplier not found: " + id));
    }

    private Supplier saveOrConflict(Supplier supplier) {
        try {
            return repository.saveAndFlush(supplier);
        } catch (DataIntegrityViolationException e) {
            // Two requests with the same email at the same moment: the unique index decides.
            throw new ConflictException(EMAIL_TAKEN);
        }
    }

    private Supplier.Details toDetails(SaveSupplierRequest in) {
        return new Supplier.Details(
                in.name().trim(),
                blankToNull(in.contactName()),
                in.contactEmail().trim().toLowerCase(Locale.ROOT),
                blankToNull(in.contactPhone()),
                in.countryCode().trim().toUpperCase(Locale.ROOT),
                blankToNull(in.websiteUrl()),
                blankToNull(in.taxId()),
                blankToNull(in.paymentTerms()),
                blankToNull(in.notes()),
                normalizeCategories(in.categories()));
    }

    /** Trims, drops blanks, removes duplicates ignoring case (first spelling wins). */
    private static List<String> normalizeCategories(List<String> raw) {
        List<String> result = new ArrayList<>();
        if (raw == null) {
            return result;
        }
        for (String c : raw) {
            if (c == null || c.isBlank()) continue;
            String trimmed = c.trim();
            boolean duplicate = result.stream().anyMatch(existing -> existing.equalsIgnoreCase(trimmed));
            if (!duplicate) result.add(trimmed);
        }
        return result;
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value.trim();
    }

    private static List<String> sortedCategories(Supplier s) {
        return s.getCategories().stream().sorted(String.CASE_INSENSITIVE_ORDER).toList();
    }

    private SupplierSummary toSummary(Supplier s) {
        return new SupplierSummary(s.getId(), s.getName(), s.getContactEmail(), s.getCountryCode(),
                s.getStatus(), sortedCategories(s));
    }

    private SupplierResponse toResponse(Supplier s) {
        return new SupplierResponse(s.getId(), s.getName(), s.getContactName(), s.getContactEmail(),
                s.getContactPhone(), s.getCountryCode(), s.getWebsiteUrl(), s.getTaxId(), s.getPaymentTerms(),
                s.getNotes(), s.getStatus(), s.getStatusReason(), sortedCategories(s),
                s.getCreatedAt(), s.getUpdatedAt());
    }
}
