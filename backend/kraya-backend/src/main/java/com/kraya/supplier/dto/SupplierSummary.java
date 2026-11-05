package com.kraya.supplier.dto;

import com.kraya.supplier.entity.SupplierStatus;

import java.util.List;
import java.util.UUID;

public record SupplierSummary(
        UUID id,
        String name,
        String contactEmail,
        String countryCode,
        SupplierStatus status,
        List<String> categories
) {
}
