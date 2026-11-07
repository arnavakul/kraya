package com.kraya.dashboard.repository;

import com.kraya.dashboard.dto.ActivityRow;
import com.kraya.dashboard.dto.CurrencyTotal;
import com.kraya.dashboard.dto.RefLabel;
import com.kraya.dashboard.dto.StatusCount;
import com.kraya.procurement.entity.ProcurementRequest;
import com.kraya.procurement.entity.RequestStatus;
import com.kraya.supplier.entity.SupplierStatus;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.Repository;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.time.LocalDate;
import java.util.Collection;
import java.util.List;
import java.util.UUID;

/**
 * Read-only aggregate queries for the dashboard. They count and sum in the database, so the
 * dashboard never loads whole tables into memory. Every query is scoped to one organization.
 */
public interface DashboardQueries extends Repository<ProcurementRequest, UUID> {

    @Query("""
            select new com.kraya.dashboard.dto.StatusCount(r.status, count(r))
            from ProcurementRequest r
            where r.organizationId = :org
            group by r.status
            """)
    List<StatusCount> countByStatus(@Param("org") UUID org);

    @Query("""
            select new com.kraya.dashboard.dto.CurrencyTotal(r.currencyCode, sum(r.budgetAmount))
            from ProcurementRequest r
            where r.organizationId = :org and r.status = :status and r.budgetAmount is not null
            group by r.currencyCode
            """)
    List<CurrencyTotal> sumBudgetByCurrency(@Param("org") UUID org, @Param("status") RequestStatus status);

    @Query("""
            select count(r) from ProcurementRequest r
            where r.organizationId = :org and r.createdAt >= :from and r.createdAt < :to
            """)
    long countCreatedBetween(@Param("org") UUID org, @Param("from") Instant from, @Param("to") Instant to);

    @Query("""
            select r from ProcurementRequest r
            where r.organizationId = :org and r.status in :statuses
            order by r.updatedAt desc
            """)
    List<ProcurementRequest> findByStatuses(@Param("org") UUID org,
                                            @Param("statuses") Collection<RequestStatus> statuses,
                                            Pageable pageable);

    @Query("""
            select count(r) from ProcurementRequest r
            where r.organizationId = :org and r.status in :statuses and r.updatedAt < :cutoff
            """)
    long countNotUpdatedSince(@Param("org") UUID org,
                              @Param("statuses") Collection<RequestStatus> statuses,
                              @Param("cutoff") Instant cutoff);

    @Query("""
            select count(r) from ProcurementRequest r
            where r.organizationId = :org and r.status in :statuses and r.neededBy < :date
            """)
    long countNeededBefore(@Param("org") UUID org,
                           @Param("statuses") Collection<RequestStatus> statuses,
                           @Param("date") LocalDate date);

    @Query("""
            select count(r) from ProcurementRequest r
            where r.organizationId = :org and r.status in :statuses
              and r.neededBy >= :from and r.neededBy <= :to
            """)
    long countNeededBetween(@Param("org") UUID org,
                            @Param("statuses") Collection<RequestStatus> statuses,
                            @Param("from") LocalDate from, @Param("to") LocalDate to);

    @Query("""
            select count(s) from Supplier s
            where s.organizationId = :org and s.status in :statuses
            """)
    long countSuppliers(@Param("org") UUID org, @Param("statuses") Collection<SupplierStatus> statuses);

    @Query("""
            select count(a) from AuditEvent a
            where a.organizationId = :org and a.entityType = :entityType and a.action = :action
              and a.newState = :newState and a.createdAt >= :from
            """)
    long countStateChangesSince(@Param("org") UUID org, @Param("entityType") String entityType,
                                @Param("action") String action, @Param("newState") String newState,
                                @Param("from") Instant from);

    @Query("""
            select new com.kraya.dashboard.dto.ActivityRow(
                a.action, a.entityType, a.entityId, a.previousState, a.newState, a.createdAt)
            from AuditEvent a
            where a.organizationId = :org
            order by a.createdAt desc
            """)
    List<ActivityRow> recentActivity(@Param("org") UUID org, Pageable pageable);

    @Query("""
            select new com.kraya.dashboard.dto.RefLabel(r.id, r.reference, r.title)
            from ProcurementRequest r
            where r.organizationId = :org and r.id in :ids
            """)
    List<RefLabel> requestLabels(@Param("org") UUID org, @Param("ids") Collection<UUID> ids);

    @Query("""
            select new com.kraya.dashboard.dto.RefLabel(s.id, s.name, s.name)
            from Supplier s
            where s.organizationId = :org and s.id in :ids
            """)
    List<RefLabel> supplierLabels(@Param("org") UUID org, @Param("ids") Collection<UUID> ids);
}
