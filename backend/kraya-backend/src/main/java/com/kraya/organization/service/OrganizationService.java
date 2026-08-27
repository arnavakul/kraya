package com.kraya.organization.service;

import com.kraya.common.exception.ResourceNotFoundException;
import com.kraya.organization.dto.CreateOrganizationRequest;
import com.kraya.organization.dto.OrganizationResponse;
import com.kraya.organization.entity.Organization;
import com.kraya.organization.entity.OrganizationStatus;
import com.kraya.organization.repository.OrganizationRepository;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class OrganizationService {

    private final OrganizationRepository organizationRepository;

    public OrganizationService(OrganizationRepository organizationRepository) {
        this.organizationRepository = organizationRepository;
    }

    @Transactional
    public OrganizationResponse create(CreateOrganizationRequest request) {

        Organization organization = new Organization();

        organization.setLegalName(request.legalName());
        organization.setTradeName(request.tradeName());
        organization.setOrganizationType(request.organizationType());
        organization.setStatus(OrganizationStatus.PENDING_VERIFICATION);
        organization.setCountryCode(request.countryCode().toUpperCase());
        organization.setPrimaryEmail(request.primaryEmail().toLowerCase());
        organization.setPrimaryPhone(request.primaryPhone());
        organization.setWebsiteUrl(request.websiteUrl());

        organization.setPreferredLanguage(
                request.preferredLanguage() != null
                        ? request.preferredLanguage()
                        : "en-IN"
        );

        organization.setCurrencyCode(
                request.currencyCode() != null
                        ? request.currencyCode().toUpperCase()
                        : "INR"
        );

        organization.setTimezone(
                request.timezone() != null
                        ? request.timezone()
                        : "Asia/Kolkata"
        );

        organization.setVerified(false);

        Organization saved = organizationRepository.save(organization);

        return toResponse(saved);
    }

    @Transactional(readOnly = true)
    public OrganizationResponse getById(UUID id) {

        Organization organization = organizationRepository.findById(id)
                .orElseThrow(() ->
                         new ResourceNotFoundException("Organization not found: " + id)
                );

        return toResponse(organization);
    }

    private OrganizationResponse toResponse(Organization organization) {

        return new OrganizationResponse(
                organization.getId(),
                organization.getLegalName(),
                organization.getTradeName(),
                organization.getOrganizationType(),
                organization.getStatus(),
                organization.getCountryCode(),
                organization.getPrimaryEmail(),
                organization.getPrimaryPhone(),
                organization.getWebsiteUrl(),
                organization.getPreferredLanguage(),
                organization.getCurrencyCode(),
                organization.getTimezone(),
                organization.isVerified(),
                organization.getCreatedAt(),
                organization.getUpdatedAt()
        );
    }
}
