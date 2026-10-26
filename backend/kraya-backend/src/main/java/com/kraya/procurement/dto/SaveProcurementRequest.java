package com.kraya.procurement.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/** Body for both create and update. */
public record SaveProcurementRequest(
        @NotBlank @Size(max = 255)
        String title,

        @Size(max = 4000)
        String description,

        @Size(max = 100)
        String category,

        @DecimalMin("0.00") @Digits(integer = 13, fraction = 2)
        BigDecimal budgetAmount,

        @Pattern(regexp = "^[A-Za-z]{3}$", message = "must be a 3-letter currency code")
        String currencyCode,

        LocalDate neededBy,

        @Size(max = 255)
        String deliveryLocation,

        @NotEmpty @Size(max = 100)
        List<@Valid ItemInput> items
) {
}
