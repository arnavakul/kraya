package com.kraya.auth.dto;

import java.util.UUID;

public record LoginResponse(

        UUID userId,
        UUID organizationId,
        String email,
        String role,
        String token

) {}