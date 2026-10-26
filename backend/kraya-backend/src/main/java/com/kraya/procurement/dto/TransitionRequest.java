package com.kraya.procurement.dto;

import com.kraya.procurement.entity.RequestStatus;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record TransitionRequest(
        @NotNull
        RequestStatus to,

        @Size(max = 500)
        String reason
) {
}
