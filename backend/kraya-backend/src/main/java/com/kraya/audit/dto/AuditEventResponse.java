package com.kraya.audit.dto;

import java.time.Instant;
import java.util.UUID;

public record AuditEventResponse(
        UUID id,
        String action,
        String previousState,
        String newState,
        String result,
        UUID actorUserId,
        String correlationId,
        Instant createdAt
) {
}
