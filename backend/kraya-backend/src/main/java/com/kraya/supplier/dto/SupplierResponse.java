package com.kraya.supplier.dto;

import com.kraya.supplier.entity.SupplierStatus;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record SupplierResponse(
        UUID id,
        String name,
        String contactName,
        String contactEmail,
        String contactPhone,
        String countryCode,
        String websiteUrl,
        String taxId,
        String paymentTerms,
        String notes,
        SupplierStatus status,
        String statusReason,
        List<String> categories,
        Instant createdAt,
        Instant updatedAt
) {
}
