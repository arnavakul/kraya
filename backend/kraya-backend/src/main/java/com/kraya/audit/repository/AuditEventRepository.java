package com.kraya.audit.repository;

import com.kraya.audit.entity.AuditEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface AuditEventRepository extends JpaRepository<AuditEvent, UUID> {

    List<AuditEvent> findByOrganizationIdAndEntityTypeAndEntityIdOrderByCreatedAtAsc(
            UUID organizationId, String entityType, UUID entityId);
}
