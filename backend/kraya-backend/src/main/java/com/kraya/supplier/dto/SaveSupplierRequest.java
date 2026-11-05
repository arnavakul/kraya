package com.kraya.supplier.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;

/** Body for both create and update. */
public record SaveSupplierRequest(
        @NotBlank @Size(max = 255)
        String name,

        @Size(max = 255)
        String contactName,

        @NotBlank @Email @Size(max = 320)
        String contactEmail,

        @Size(max = 30)
        String contactPhone,

        @NotBlank @Size(min = 2, max = 2)
        String countryCode,

        @Size(max = 500)
        String websiteUrl,

        @Size(max = 50)
        String taxId,

        @Size(max = 255)
        String paymentTerms,

        @Size(max = 2000)
        String notes,

        @Size(max = 20)
        List<@NotBlank @Size(max = 100) String> categories
) {
}
