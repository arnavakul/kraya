package com.kraya.common.security;

import com.kraya.user.entity.UserRole;

import java.util.UUID;

/** The authenticated caller, resolved fresh from the database on each request. */
public record CurrentUser(UUID userId, UUID organizationId, UserRole role) {

    public boolean canManageProcurement() {
        return role == UserRole.ORG_ADMIN || role == UserRole.PROCUREMENT;
    }
}
