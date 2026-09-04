package com.kraya.user.repository;

import com.kraya.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID> {

    boolean existsByOrganizationIdAndEmail(
            UUID organizationId,
            String email
    );

    List<User> findByOrganizationId(UUID organizationId);
}