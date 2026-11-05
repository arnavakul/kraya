package com.kraya.supplier.dto;

import com.kraya.supplier.entity.SupplierStatus;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record SupplierStatusRequest(
        @NotNull
        SupplierStatus status,

        @Size(max = 500)
        String reason
) {
}
