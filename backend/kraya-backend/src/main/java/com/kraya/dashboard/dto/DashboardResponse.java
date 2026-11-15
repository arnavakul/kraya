package com.kraya.dashboard.dto;

import com.kraya.procurement.entity.RequestStatus;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public record DashboardResponse(
        Summary summary,
        List<PipelineSlice> pipeline,
        List<ActiveRequest> activeRequests,
        List<ActivityItem> recentActivity,
        List<Insight> insights,
        Instant generatedAt
) {

    public record Summary(
            long totalRequests,
            long requestsLast30Days,
            long requestsPrevious30Days,
            long activeRequests,
            long completedRequests,
            long completedLast30Days,
            long pendingApprovals,
            long activeSuppliers,
            List<SpendByCurrency> spend
    ) {
    }

    /** Budgets of completed requests, per currency (currencies are never added together). */
    public record SpendByCurrency(String currency, BigDecimal amount) {
    }

    public record PipelineSlice(String key, String label, long count) {
    }

    public record ActiveRequest(
            UUID id,
            String reference,
            String title,
            RequestStatus status,
            int progressPercent,
            BigDecimal budgetAmount,
            String currencyCode,
            LocalDate neededBy,
            Instant updatedAt
    ) {
    }

    public record ActivityItem(
            String action,
            String entityType,
            UUID entityId,
            String entityLabel,
            String entitySubLabel,
            String previousState,
            String newState,
            Instant createdAt
    ) {
    }

    /** severity is "warning", "info" or "ok". */
    public record Insight(String severity, String message) {
    }
}
