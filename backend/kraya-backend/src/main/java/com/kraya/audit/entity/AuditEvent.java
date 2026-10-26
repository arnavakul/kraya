package com.kraya.audit.entity;

import jakarta.persistence.*;

import java.time.Instant;
import java.util.UUID;

/** Immutable audit record: written once, never updated. */
@Entity
@Table(name = "audit_events")
public class AuditEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "organization_id", nullable = false, updatable = false)
    private UUID organizationId;

    @Column(name = "correlation_id", length = 64, updatable = false)
    private String correlationId;

    @Column(name = "actor_user_id", updatable = false)
    private UUID actorUserId;

    @Column(nullable = false, length = 60, updatable = false)
    private String action;

    @Column(name = "entity_type", nullable = false, length = 60, updatable = false)
    private String entityType;

    @Column(name = "entity_id", nullable = false, updatable = false)
    private UUID entityId;

    @Column(name = "previous_state", length = 30, updatable = false)
    private String previousState;

    @Column(name = "new_state", length = 30, updatable = false)
    private String newState;

    @Column(nullable = false, length = 20, updatable = false)
    private String result = "SUCCESS";

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    protected AuditEvent() {
    }

    public AuditEvent(UUID organizationId, String correlationId, UUID actorUserId, String action,
                      String entityType, UUID entityId, String previousState, String newState) {
        this.organizationId = organizationId;
        this.correlationId = correlationId;
        this.actorUserId = actorUserId;
        this.action = action;
        this.entityType = entityType;
        this.entityId = entityId;
        this.previousState = previousState;
        this.newState = newState;
    }

    public UUID getId() { return id; }
    public String getCorrelationId() { return correlationId; }
    public UUID getActorUserId() { return actorUserId; }
    public String getAction() { return action; }
    public String getPreviousState() { return previousState; }
    public String getNewState() { return newState; }
    public String getResult() { return result; }
    public Instant getCreatedAt() { return createdAt; }
}
