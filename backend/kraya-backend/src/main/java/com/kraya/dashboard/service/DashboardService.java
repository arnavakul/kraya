package com.kraya.dashboard.service;

import com.kraya.common.security.CurrentUser;
import com.kraya.common.security.CurrentUserProvider;
import com.kraya.dashboard.dto.ActivityRow;
import com.kraya.dashboard.dto.CurrencyTotal;
import com.kraya.dashboard.dto.DashboardResponse;
import com.kraya.dashboard.dto.DashboardResponse.ActiveRequest;
import com.kraya.dashboard.dto.DashboardResponse.ActivityItem;
import com.kraya.dashboard.dto.DashboardResponse.Insight;
import com.kraya.dashboard.dto.DashboardResponse.PipelineSlice;
import com.kraya.dashboard.dto.DashboardResponse.SpendByCurrency;
import com.kraya.dashboard.dto.DashboardResponse.Summary;
import com.kraya.dashboard.dto.RefLabel;
import com.kraya.dashboard.repository.DashboardQueries;
import com.kraya.organization.repository.OrganizationRepository;
import com.kraya.procurement.entity.ProcurementRequest;
import com.kraya.procurement.entity.RequestStatus;
import com.kraya.supplier.entity.SupplierStatus;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.DateTimeException;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class DashboardService {

    private static final String REQUEST_TYPE = "PROCUREMENT_REQUEST";
    private static final String SUPPLIER_TYPE = "SUPPLIER";

    /** Requests the team is actively working on (everything between submission and completion). */
    private static final Set<RequestStatus> ACTIVE = Collections.unmodifiableSet(EnumSet.of(
            RequestStatus.SUBMITTED, RequestStatus.VALIDATING, RequestStatus.SOURCING, RequestStatus.QUOTING,
            RequestStatus.EVALUATION, RequestStatus.NEGOTIATION, RequestStatus.APPROVAL, RequestStatus.PO_DRAFT));

    private static final Set<RequestStatus> OPEN = Collections.unmodifiableSet(openStatuses());

    private static final Set<RequestStatus> NOT_YET_APPROVED = Collections.unmodifiableSet(EnumSet.of(
            RequestStatus.DRAFT, RequestStatus.SUBMITTED, RequestStatus.VALIDATING, RequestStatus.SOURCING,
            RequestStatus.QUOTING, RequestStatus.EVALUATION, RequestStatus.NEGOTIATION));

    /** The happy path, used to turn a status into a progress percentage. */
    private static final List<RequestStatus> FLOW = List.of(
            RequestStatus.DRAFT, RequestStatus.SUBMITTED, RequestStatus.VALIDATING, RequestStatus.SOURCING,
            RequestStatus.QUOTING, RequestStatus.EVALUATION, RequestStatus.NEGOTIATION, RequestStatus.APPROVAL,
            RequestStatus.PO_DRAFT, RequestStatus.COMPLETED);

    private static final int WINDOW_DAYS = 30;
    private static final int DUE_SOON_DAYS = 14;
    private static final int STALLED_DAYS = 7;
    private static final int ACTIVE_LIMIT = 5;
    private static final int ACTIVITY_LIMIT = 8;

    private final DashboardQueries queries;
    private final OrganizationRepository organizationRepository;
    private final CurrentUserProvider currentUserProvider;

    public DashboardService(DashboardQueries queries, OrganizationRepository organizationRepository,
                            CurrentUserProvider currentUserProvider) {
        this.queries = queries;
        this.organizationRepository = organizationRepository;
        this.currentUserProvider = currentUserProvider;
    }

    private static Set<RequestStatus> openStatuses() {
        Set<RequestStatus> open = EnumSet.copyOf(ACTIVE);
        open.add(RequestStatus.DRAFT);
        return open;
    }

    @Transactional(readOnly = true)
    public DashboardResponse load() {
        CurrentUser user = currentUserProvider.require();
        UUID org = user.organizationId();
        Instant now = Instant.now();
        LocalDate today = LocalDate.now(zoneOf(org));

        Map<RequestStatus, Long> byStatus = new EnumMap<>(RequestStatus.class);
        queries.countByStatus(org).forEach(row -> byStatus.put(row.status(), row.count()));

        long total = byStatus.values().stream().mapToLong(Long::longValue).sum();
        long active = count(byStatus, ACTIVE.toArray(new RequestStatus[0]));
        long completed = count(byStatus, RequestStatus.COMPLETED);
        long pendingApprovals = count(byStatus, RequestStatus.APPROVAL);

        Instant windowStart = now.minus(Duration.ofDays(WINDOW_DAYS));
        long unavailableSuppliers = queries.countSuppliers(org, EnumSet.of(SupplierStatus.INACTIVE, SupplierStatus.BLOCKED));

        Summary summary = new Summary(
                total,
                queries.countCreatedBetween(org, windowStart, now),
                queries.countCreatedBetween(org, now.minus(Duration.ofDays(2L * WINDOW_DAYS)), windowStart),
                active,
                completed,
                queries.countStateChangesSince(org, REQUEST_TYPE, "REQUEST_STATUS_CHANGED", "COMPLETED", windowStart),
                pendingApprovals,
                queries.countSuppliers(org, EnumSet.of(SupplierStatus.ACTIVE)),
                spend(org));

        return new DashboardResponse(
                summary,
                pipeline(byStatus),
                activeRequests(org),
                recentActivity(org),
                insights(org, now, today, pendingApprovals, unavailableSuppliers),
                now);
    }

    // ---------- sections ----------

    private List<PipelineSlice> pipeline(Map<RequestStatus, Long> by) {
        return List.of(
                new PipelineSlice("draft", "Draft", count(by, RequestStatus.DRAFT)),
                new PipelineSlice("submitted", "Submitted", count(by, RequestStatus.SUBMITTED)),
                new PipelineSlice("in_progress", "In progress", count(by, RequestStatus.VALIDATING,
                        RequestStatus.SOURCING, RequestStatus.QUOTING, RequestStatus.EVALUATION,
                        RequestStatus.NEGOTIATION, RequestStatus.PO_DRAFT)),
                new PipelineSlice("pending_approval", "Pending approval", count(by, RequestStatus.APPROVAL)),
                new PipelineSlice("completed", "Completed", count(by, RequestStatus.COMPLETED)),
                new PipelineSlice("closed", "Rejected or cancelled",
                        count(by, RequestStatus.REJECTED, RequestStatus.CANCELLED)));
    }

    private List<SpendByCurrency> spend(UUID org) {
        return queries.sumBudgetByCurrency(org, RequestStatus.COMPLETED).stream()
                .sorted(Comparator.comparing(CurrencyTotal::total).reversed())
                .map(t -> new SpendByCurrency(t.currency(), t.total()))
                .toList();
    }

    private List<ActiveRequest> activeRequests(UUID org) {
        return queries.findByStatuses(org, ACTIVE, PageRequest.of(0, ACTIVE_LIMIT)).stream()
                .map(r -> new ActiveRequest(r.getId(), r.getReference(), r.getTitle(), r.getStatus(),
                        progress(r), r.getBudgetAmount(), r.getCurrencyCode(), r.getNeededBy(), r.getUpdatedAt()))
                .toList();
    }

    private static int progress(ProcurementRequest r) {
        int index = FLOW.indexOf(r.getStatus());
        return index < 0 ? 0 : index * 100 / (FLOW.size() - 1);
    }

    private List<ActivityItem> recentActivity(UUID org) {
        List<ActivityRow> rows = queries.recentActivity(org, PageRequest.of(0, ACTIVITY_LIMIT));

        Map<UUID, RefLabel> requests = labels(rows, REQUEST_TYPE, ids -> queries.requestLabels(org, ids));
        Map<UUID, RefLabel> suppliers = labels(rows, SUPPLIER_TYPE, ids -> queries.supplierLabels(org, ids));

        return rows.stream().map(row -> {
            RefLabel label = switch (row.entityType()) {
                case REQUEST_TYPE -> requests.get(row.entityId());
                case SUPPLIER_TYPE -> suppliers.get(row.entityId());
                default -> null;
            };
            return new ActivityItem(row.action(), row.entityType(), row.entityId(),
                    label == null ? null : label.label(),
                    label == null || SUPPLIER_TYPE.equals(row.entityType()) ? null : label.subLabel(),
                    row.previousState(), row.newState(), row.createdAt());
        }).toList();
    }

    private static Map<UUID, RefLabel> labels(List<ActivityRow> rows, String entityType,
                                              Function<Set<UUID>, List<RefLabel>> lookup) {
        Set<UUID> ids = rows.stream().filter(r -> entityType.equals(r.entityType()))
                .map(ActivityRow::entityId).collect(Collectors.toSet());
        if (ids.isEmpty()) {
            return Map.of();
        }
        return lookup.apply(ids).stream().collect(Collectors.toMap(RefLabel::id, Function.identity()));
    }

    /** Plain rules over the team's own data. No AI involved, so every line can be explained. */
    private List<Insight> insights(UUID org, Instant now, LocalDate today,
                                   long pendingApprovals, long unavailableSuppliers) {
        List<Insight> list = new ArrayList<>();

        long overdue = queries.countNeededBefore(org, OPEN, today);
        if (overdue > 0) {
            list.add(new Insight("warning", plural(overdue, "request") + (overdue == 1 ? " is" : " are")
                    + " past the needed-by date and still open."));
        }

        long dueSoon = queries.countNeededBetween(org, NOT_YET_APPROVED, today, today.plusDays(DUE_SOON_DAYS));
        if (dueSoon > 0) {
            list.add(new Insight("warning", plural(dueSoon, "request") + (dueSoon == 1 ? " is" : " are")
                    + " needed within " + DUE_SOON_DAYS + " days but not yet at approval."));
        }

        long stalled = queries.countNotUpdatedSince(org, ACTIVE, now.minus(Duration.ofDays(STALLED_DAYS)));
        if (stalled > 0) {
            list.add(new Insight("warning", plural(stalled, "active request") + (stalled == 1 ? " hasn't" : " haven't")
                    + " moved in " + STALLED_DAYS + "+ days."));
        }

        if (list.isEmpty()) {
            list.add(new Insight("ok", "Nothing is overdue or stalled."));
        }

        if (pendingApprovals > 0) {
            list.add(new Insight("info", plural(pendingApprovals, "request") + (pendingApprovals == 1 ? " is" : " are")
                    + " waiting for approval."));
        }
        if (unavailableSuppliers > 0) {
            list.add(new Insight("info", plural(unavailableSuppliers, "supplier") + (unavailableSuppliers == 1 ? " is" : " are")
                    + " inactive or blocked and won't receive RFQs."));
        }
        return list;
    }

    // ---------- helpers ----------

    private ZoneId zoneOf(UUID org) {
        return organizationRepository.findById(org)
                .map(o -> {
                    try {
                        return ZoneId.of(o.getTimezone());
                    } catch (DateTimeException | NullPointerException e) {
                        return (ZoneId) ZoneOffset.UTC;
                    }
                })
                .orElse(ZoneOffset.UTC);
    }

    private static long count(Map<RequestStatus, Long> by, RequestStatus... statuses) {
        long sum = 0;
        for (RequestStatus s : statuses) {
            sum += by.getOrDefault(s, 0L);
        }
        return sum;
    }

    private static String plural(long n, String noun) {
        return n + " " + noun + (n == 1 ? "" : "s");
    }
}
