package com.kraya.user.service;

import com.kraya.common.exception.ResourceNotFoundException;
import com.kraya.organization.entity.Organization;
import com.kraya.organization.repository.OrganizationRepository;
import com.kraya.user.dto.CreateUserRequest;
import com.kraya.user.dto.UpdateUserRequest;
import com.kraya.user.dto.UserResponse;
import com.kraya.user.entity.User;
import com.kraya.user.entity.UserStatus;
import com.kraya.user.repository.UserRepository;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Locale;
import java.util.UUID;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final OrganizationRepository organizationRepository;
    private final BCryptPasswordEncoder passwordEncoder;

    public UserService(
            UserRepository userRepository,
            OrganizationRepository organizationRepository
    ) {
        this.userRepository = userRepository;
        this.organizationRepository = organizationRepository;
        this.passwordEncoder = new BCryptPasswordEncoder();
    }

    @Transactional
    public UserResponse create(CreateUserRequest request) {

        Organization organization = organizationRepository
                .findById(request.organizationId())
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Organization not found: " + request.organizationId()
                        )
                );

        String normalizedEmail = request.email()
                .trim()
                .toLowerCase(Locale.ROOT);

        if (userRepository.existsByOrganizationIdAndEmail(
                organization.getId(),
                normalizedEmail
        )) {
            throw new IllegalArgumentException(
                    "User with this email already exists in this organization"
            );
        }

        User user = new User();

        user.setOrganization(organization);
        user.setEmail(normalizedEmail);
        user.setFirstName(request.firstName().trim());
        user.setLastName(request.lastName().trim());

        // Never store plain passwords
        user.setPasswordHash(
                passwordEncoder.encode(request.password())
        );

        user.setRole(request.role());
        user.setStatus(UserStatus.ACTIVE);

        User saved = userRepository.save(user);

        return toResponse(saved);
    }

    @Transactional(readOnly = true)
    public UserResponse getById(UUID id) {

        User user = userRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "User not found: " + id
                        )
                );

        return toResponse(user);
    }

    private UserResponse toResponse(User user) {

        return new UserResponse(
                user.getId(),
                user.getOrganization().getId(),
                user.getEmail(),
                user.getFirstName(),
                user.getLastName(),
                user.getRole(),
                user.getStatus(),
                user.getCreatedAt(),
                user.getUpdatedAt()
        );
    }

    @Transactional(readOnly = true)
    public List<UserResponse> getByOrganizationId(UUID orgainzationId) {
        if(!organizationRepository.existsById(orgainzationId)) {
            throw new ResourceNotFoundException(
                    "Organization not found: " + orgainzationId
            );
        }

        return userRepository.findByOrganizationId(orgainzationId)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional
    public UserResponse update(UUID id, UpdateUserRequest request) {
        User user = userRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "User not found: " + id
                        ));

        if (request.firstName() != null) {
            user.setFirstName(request.firstName().trim());
        }

        if (request.lastName() != null) {
            user.setLastName(request.lastName().trim());
        }

        if (request.role() != null) {
            user.setRole(request.role());
        }

        if (request.status() != null) {
            user.setStatus(request.status());
        }

        User updated = userRepository.save(user);

        return toResponse(updated);
    }

    @Transactional
    public UserResponse suspend(UUID id) {

        User user = userRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "User not found: " + id
                        )
                );

        user.setStatus(UserStatus.SUSPENDED);

        User updated = userRepository.save(user);

        return toResponse(updated);
    }
}