package com.kraya.procurement.dto;

import java.math.BigDecimal;
import java.util.UUID;

public record ItemResponse(
        UUID id,
        int lineNo,
        String name,
        String description,
        BigDecimal quantity,
        String unit
) {
}
