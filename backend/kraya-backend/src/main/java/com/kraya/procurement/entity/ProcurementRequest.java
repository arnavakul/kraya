package com.kraya.procurement.entity;

import com.kraya.common.exception.BadRequestException;
import com.kraya.common.exception.ConflictException;
import jakarta.persistence.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "procurement_requests")
public class ProcurementRequest {

    /** Plain data for one line item; the entity turns it into numbered child rows. */
    public record ItemData(String name, String description, BigDecimal quantity, String unit) {
    }

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    // Referenced by id, not by entity: modules stay decoupled.
    @Column(name = "organization_id", nullable = false, updatable = false)
    private UUID organizationId;

    @Column(nullable = false, unique = true, length = 30, updatable = false)
    private String reference;

    @Column(nullable = false, length = 255)
    private String title;

    @Column(length = 4000)
    private String description;

    @Column(length = 100)
    private String category;

    @Column(name = "budget_amount", precision = 15, scale = 2)
    private BigDecimal budgetAmount;

    @Column(name = "currency_code", nullable = false, length = 3)
    private String currencyCode = "INR";

    @Column(name = "needed_by")
    private LocalDate neededBy;

    @Column(name = "delivery_location", length = 255)
    private String deliveryLocation;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private RequestStatus status = RequestStatus.DRAFT;

    @Column(name = "status_reason", length = 500)
    private String statusReason;

    @Column(name = "created_by", nullable = false, updatable = false)
    private UUID createdBy;

    @Version
    private long version;

    @OneToMany(mappedBy = "request", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("lineNo ASC")
    private List<ProcurementRequestItem> items = new ArrayList<>();

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected ProcurementRequest() {
    }

    public static ProcurementRequest draft(UUID organizationId, UUID createdBy, String reference) {
        ProcurementRequest r = new ProcurementRequest();
        r.organizationId = organizationId;
        r.createdBy = createdBy;
        r.reference = reference;
        return r;
    }

    @PrePersist
    void onCreate() {
        Instant now = Instant.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = Instant.now();
    }

    /** Details can only change while the request is still a draft. */
    public void updateDetails(String title, String description, String category, BigDecimal budgetAmount,
                              String currencyCode, LocalDate neededBy, String deliveryLocation,
                              List<ItemData> newItems) {
        if (status != RequestStatus.DRAFT) {
            throw new ConflictException("Only draft requests can be edited (current status: " + status + ")");
        }
        this.title = title;
        this.description = description;
        this.category = category;
        this.budgetAmount = budgetAmount;
        this.currencyCode = currencyCode;
        this.neededBy = neededBy;
        this.deliveryLocation = deliveryLocation;

        items.clear();
        int line = 1;
        for (ItemData d : newItems) {
            items.add(new ProcurementRequestItem(this, line++, d.name(), d.description(), d.quantity(), d.unit()));
        }
    }

    /** The only place a status changes, so every path obeys the state machine. */
    public void transitionTo(RequestStatus next, String reason) {
        if (!status.canMoveTo(next)) {
            throw new ConflictException("Cannot move request from " + status + " to " + next);
        }
        if (next.requiresReason() && (reason == null || reason.isBlank())) {
            throw new BadRequestException("A reason is required to move a request to " + next);
        }
        this.status = next;
        this.statusReason = next.requiresReason() ? reason.trim() : null;
    }

    public UUID getId() { return id; }
    public String getReference() { return reference; }
    public String getTitle() { return title; }
    public String getDescription() { return description; }
    public String getCategory() { return category; }
    public BigDecimal getBudgetAmount() { return budgetAmount; }
    public String getCurrencyCode() { return currencyCode; }
    public LocalDate getNeededBy() { return neededBy; }
    public String getDeliveryLocation() { return deliveryLocation; }
    public RequestStatus getStatus() { return status; }
    public String getStatusReason() { return statusReason; }
    public UUID getCreatedBy() { return createdBy; }
    public List<ProcurementRequestItem> getItems() { return items; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
}
