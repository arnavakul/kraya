package com.kraya.dashboard.dto;

import com.kraya.procurement.entity.RequestStatus;

public record StatusCount(RequestStatus status, Long count) {
}
