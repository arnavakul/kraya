package com.kraya.user.dto;

import com.kraya.user.entity.UserRole;
import com.kraya.user.entity.UserStatus;
import jakarta.validation.constraints.Size;

public record UpdateUserRequest(

        @Size(max = 100)
        String firstName,

        @Size(max = 100)
        String lastName,

        UserRole role,

        UserStatus status

) {
}