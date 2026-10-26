package com.kraya.procurement.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public record ItemInput(
        @NotBlank @Size(max = 255)
        String name,

        @Size(max = 2000)
        String description,

        @NotNull @DecimalMin("0.001") @Digits(integer = 11, fraction = 3)
        BigDecimal quantity,

        @NotBlank @Size(max = 30)
        String unit
) {
}
