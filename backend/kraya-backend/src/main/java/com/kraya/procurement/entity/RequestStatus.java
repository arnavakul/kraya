package com.kraya.procurement.entity;

import java.util.EnumMap;
import java.util.EnumSet;
import java.util.Map;
import java.util.Set;

public enum RequestStatus {
    DRAFT, SUBMITTED, VALIDATING, SOURCING, QUOTING, EVALUATION,
    NEGOTIATION, APPROVAL, PO_DRAFT, COMPLETED, REJECTED, CANCELLED;

    private static final Map<RequestStatus, Set<RequestStatus>> NEXT = new EnumMap<>(RequestStatus.class);

    static {
        NEXT.put(DRAFT,       EnumSet.of(SUBMITTED, CANCELLED));
        NEXT.put(SUBMITTED,   EnumSet.of(VALIDATING, REJECTED, CANCELLED));
        NEXT.put(VALIDATING,  EnumSet.of(SOURCING, REJECTED, CANCELLED));
        NEXT.put(SOURCING,    EnumSet.of(QUOTING, CANCELLED));
        NEXT.put(QUOTING,     EnumSet.of(EVALUATION, CANCELLED));
        NEXT.put(EVALUATION,  EnumSet.of(NEGOTIATION, APPROVAL, CANCELLED));
        NEXT.put(NEGOTIATION, EnumSet.of(EVALUATION, APPROVAL, CANCELLED));
        NEXT.put(APPROVAL,    EnumSet.of(PO_DRAFT, REJECTED, CANCELLED));
        NEXT.put(PO_DRAFT,    EnumSet.of(COMPLETED, CANCELLED));
        // COMPLETED, REJECTED and CANCELLED are terminal.
    }

    public Set<RequestStatus> allowedNext() {
        Set<RequestStatus> next = NEXT.get(this);
        return next == null ? EnumSet.noneOf(RequestStatus.class) : EnumSet.copyOf(next);
    }

    public boolean canMoveTo(RequestStatus target) {
        Set<RequestStatus> next = NEXT.get(this);
        return next != null && next.contains(target);
    }

    public boolean isTerminal() {
        return !NEXT.containsKey(this);
    }

    public boolean requiresReason() {
        return this == REJECTED || this == CANCELLED;
    }
}
