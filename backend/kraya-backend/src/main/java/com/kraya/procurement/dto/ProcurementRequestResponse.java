package com.kraya.procurement.dto;

import com.kraya.procurement.entity.RequestStatus;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public record ProcurementRequestResponse(
        UUID id,
        String reference,
        String title,
        String description,
        String category,
        BigDecimal budgetAmount,
        String currencyCode,
        LocalDate neededBy,
        String deliveryLocation,
        RequestStatus status,
        String statusReason,
        UUID createdBy,
        List<ItemResponse> items,
        List<RequestStatus> allowedNextStatuses,
        Instant createdAt,
        Instant updatedAt
) {
}
