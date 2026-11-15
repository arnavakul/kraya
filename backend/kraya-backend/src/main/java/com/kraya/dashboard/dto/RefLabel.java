package com.kraya.dashboard.dto;

import java.util.UUID;

/** A human-readable name for an id that appears in the audit trail. */
public record RefLabel(UUID id, String label, String subLabel) {
}
