package com.kraya.supplier.repository;

import com.kraya.supplier.entity.Supplier;
import com.kraya.supplier.entity.SupplierStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.Optional;
import java.util.UUID;

public interface SupplierRepository extends JpaRepository<Supplier, UUID> {

    // Every lookup is scoped to the caller's organization (tenant isolation).
    Optional<Supplier> findByIdAndOrganizationId(UUID id, UUID organizationId);

    boolean existsByOrganizationIdAndContactEmail(UUID organizationId, String contactEmail);

    /** pattern is already lower-cased and wrapped in % by the service. */
    @Query("""
            select s from Supplier s
            where s.organizationId = :orgId
              and s.status in :statuses
              and (lower(s.name) like :pattern or s.contactEmail like :pattern)
            """)
    Page<Supplier> search(@Param("orgId") UUID orgId,
                          @Param("statuses") Collection<SupplierStatus> statuses,
                          @Param("pattern") String pattern,
                          Pageable pageable);
}
