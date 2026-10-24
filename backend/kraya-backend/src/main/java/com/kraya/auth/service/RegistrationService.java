package com.kraya.auth.service;

import com.kraya.auth.dto.RegisterRequest;
import com.kraya.common.exception.ConflictException;
import com.kraya.organization.dto.CreateOrganizationRequest;
import com.kraya.organization.dto.OrganizationResponse;
import com.kraya.organization.entity.OrganizationType;
import com.kraya.organization.repository.OrganizationRepository;
import com.kraya.organization.service.OrganizationService;
import com.kraya.user.entity.User;
import com.kraya.user.entity.UserRole;
import com.kraya.user.entity.UserStatus;
import com.kraya.user.repository.UserRepository;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Self-service signup: creates the organization and its first ORG_ADMIN user atomically. */
@Service
public class RegistrationService {

    private static final String EMAIL_TAKEN = "An account with this email already exists";

    private final OrganizationService organizationService;
    private final OrganizationRepository organizationRepository;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public RegistrationService(
            OrganizationService organizationService,
            OrganizationRepository organizationRepository,
            UserRepository userRepository,
            PasswordEncoder passwordEncoder
    ) {
        this.organizationService = organizationService;
        this.organizationRepository = organizationRepository;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public void register(RegisterRequest request) {
        String email = request.email().trim().toLowerCase();

        if (userRepository.findByEmail(email).isPresent()) {
            throw new ConflictException(EMAIL_TAKEN);
        }

        // Reuses OrganizationService validation and defaults (PENDING_VERIFICATION, INR, Asia/Kolkata).
        OrganizationResponse org = organizationService.create(new CreateOrganizationRequest(
                request.organizationName().trim(),
                null,
                OrganizationType.BUYER,
                request.countryCode().trim().toUpperCase(),
                email,
                null, null, null, null, null
        ));

        User user = new User();
        user.setOrganization(organizationRepository.getReferenceById(org.id()));
        user.setEmail(email);
        user.setFirstName(request.firstName().trim());
        user.setLastName(request.lastName().trim());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setRole(UserRole.ORG_ADMIN);
        user.setStatus(UserStatus.ACTIVE);

        try {
            userRepository.saveAndFlush(user);
        } catch (DataIntegrityViolationException e) {
            // Two signups with the same email at the same moment: the unique constraint decides.
            throw new ConflictException(EMAIL_TAKEN);
        }
    }
}