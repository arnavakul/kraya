package com.kraya.user.dto;

import com.kraya.user.entity.UserRole;
import com.kraya.user.entity.UserStatus;

import java.time.Instant;
import java.util.UUID;

public record UserResponse(

        UUID id,

        UUID organizationId,

        String email,

        String firstName,

        String lastName,

        UserRole role,

        UserStatus status,

        Instant createdAt,

        Instant updatedAt

) {
}