package com.kraya.dashboard.dto;

import java.time.Instant;
import java.util.UUID;

public record ActivityRow(String action, String entityType, UUID entityId,
                          String previousState, String newState, Instant createdAt) {
}
