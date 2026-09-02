package com.kraya.organization.dto;

import com.kraya.organization.entity.OrganizationStatus;
import com.kraya.organization.entity.OrganizationType;

import java.time.Instant;
import java.util.UUID;

public record OrganizationResponse(
        UUID id,
        String legalName,
        String tradeName,
        OrganizationType organizationType,
        OrganizationStatus status,
        String countryCode,
        String primaryEmail,
        String primaryPhone,
        String websiteUrl,
        String preferredLanguage,
        String currencyCode,
        String timezone,
        boolean verified,
        Instant createdAt,
        Instant updatedAt
) {
}
