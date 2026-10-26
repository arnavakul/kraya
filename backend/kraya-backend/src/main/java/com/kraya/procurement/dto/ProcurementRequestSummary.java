package com.kraya.procurement.dto;

import com.kraya.procurement.entity.RequestStatus;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

public record ProcurementRequestSummary(
        UUID id,
        String reference,
        String title,
        RequestStatus status,
        BigDecimal budgetAmount,
        String currencyCode,
        LocalDate neededBy,
        Instant createdAt
) {
}
