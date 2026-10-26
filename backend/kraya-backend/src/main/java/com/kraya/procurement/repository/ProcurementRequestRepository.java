package com.kraya.procurement.repository;

import com.kraya.procurement.entity.ProcurementRequest;
import com.kraya.procurement.entity.RequestStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.Optional;
import java.util.UUID;

public interface ProcurementRequestRepository extends JpaRepository<ProcurementRequest, UUID> {

    // Every lookup is scoped to the caller's organization (tenant isolation).
    Optional<ProcurementRequest> findByIdAndOrganizationId(UUID id, UUID organizationId);

    Page<ProcurementRequest> findByOrganizationId(UUID organizationId, Pageable pageable);

    Page<ProcurementRequest> findByOrganizationIdAndStatus(UUID organizationId, RequestStatus status, Pageable pageable);

    @Query(value = "select nextval('procurement_request_seq')", nativeQuery = true)
    long nextReferenceNumber();
}
