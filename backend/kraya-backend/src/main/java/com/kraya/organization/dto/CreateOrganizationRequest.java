package com.kraya.organization.dto;

import com.kraya.organization.entity.OrganizationType;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateOrganizationRequest(
        @NotBlank
        @Size(max = 255)
        String legalName,

        @Size(max = 255)
        String tradeName,

        @NotNull
        OrganizationType organizationType,

        @NotBlank
        @Size(min = 2, max = 2)
        String countryCode,

        @NotBlank
        @Email
        @Size(max = 320)
        String primaryEmail,

        @Size(max = 30)
        String primaryPhone,

        @Size(max = 500)
        String websiteUrl,

        @Size(max = 10)
        String preferredLanguage,

        @Size(min = 3, max = 3)
        String currencyCode,

        @Size(max = 50)
        String timezone
) {
}
