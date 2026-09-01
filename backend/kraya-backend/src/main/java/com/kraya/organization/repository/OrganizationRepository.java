package com.kraya.organization.repository;

import com.kraya.organization.entity.Organization;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface OrganizationRepository extends JpaRepository<Organization, UUID> {
    boolean existsByPrimaryEmailIgnoreCase(String primaryEmail);
}