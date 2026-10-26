package com.kraya.audit.service;

import com.kraya.audit.dto.AuditEventResponse;
import com.kraya.audit.entity.AuditEvent;
import com.kraya.audit.repository.AuditEventRepository;
import com.kraya.common.security.CurrentUser;
import com.kraya.common.web.CorrelationIdFilter;
import org.slf4j.MDC;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class AuditService {

    private final AuditEventRepository repository;

    public AuditService(AuditEventRepository repository) {
        this.repository = repository;
    }

    /** Joins the caller's transaction, so the audit row commits or rolls back with the change itself. */
    @Transactional
    public void record(CurrentUser actor, String action, String entityType, UUID entityId,
                       String previousState, String newState) {
        repository.save(new AuditEvent(
                actor.organizationId(),
                MDC.get(CorrelationIdFilter.MDC_KEY),
                actor.userId(),
                action, entityType, entityId, previousState, newState));
    }

    @Transactional(readOnly = true)
    public List<AuditEventResponse> history(UUID organizationId, String entityType, UUID entityId) {
        return repository
                .findByOrganizationIdAndEntityTypeAndEntityIdOrderByCreatedAtAsc(organizationId, entityType, entityId)
                .stream()
                .map(e -> new AuditEventResponse(e.getId(), e.getAction(), e.getPreviousState(), e.getNewState(),
                        e.getResult(), e.getActorUserId(), e.getCorrelationId(), e.getCreatedAt()))
                .toList();
    }
}
