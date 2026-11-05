package com.kraya.supplier.entity;

import com.kraya.common.exception.BadRequestException;
import com.kraya.common.exception.ConflictException;
import jakarta.persistence.*;
import org.hibernate.annotations.BatchSize;

import java.time.Instant;
import java.util.Collection;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.UUID;

@Entity
@Table(name = "suppliers")
public class Supplier {

    /** Editable fields, already trimmed and normalized by the service. */
    public record Details(
            String name, String contactName, String contactEmail, String contactPhone,
            String countryCode, String websiteUrl, String taxId, String paymentTerms,
            String notes, Collection<String> categories) {
    }

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "organization_id", nullable = false, updatable = false)
    private UUID organizationId;

    @Column(nullable = false, length = 255)
    private String name;

    @Column(name = "contact_name", length = 255)
    private String contactName;

    @Column(name = "contact_email", nullable = false, length = 320)
    private String contactEmail;

    @Column(name = "contact_phone", length = 30)
    private String contactPhone;

    @Column(name = "country_code", nullable = false, length = 2)
    private String countryCode;

    @Column(name = "website_url", length = 500)
    private String websiteUrl;

    @Column(name = "tax_id", length = 50)
    private String taxId;

    @Column(name = "payment_terms", length = 255)
    private String paymentTerms;

    @Column(length = 2000)
    private String notes;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private SupplierStatus status = SupplierStatus.ACTIVE;

    @Column(name = "status_reason", length = 500)
    private String statusReason;

    @ElementCollection(fetch = FetchType.LAZY)
    @CollectionTable(name = "supplier_categories", joinColumns = @JoinColumn(name = "supplier_id"))
    @Column(name = "category", nullable = false, length = 100)
    @BatchSize(size = 50) // list pages load categories in batches, not one query per row
    private Set<String> categories = new LinkedHashSet<>();

    @Column(name = "created_by", nullable = false, updatable = false)
    private UUID createdBy;

    @Version
    private long version;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected Supplier() {
    }

    public static Supplier create(UUID organizationId, UUID createdBy) {
        Supplier s = new Supplier();
        s.organizationId = organizationId;
        s.createdBy = createdBy;
        return s;
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

    public void updateDetails(Details d) {
        this.name = d.name();
        this.contactName = d.contactName();
        this.contactEmail = d.contactEmail();
        this.contactPhone = d.contactPhone();
        this.countryCode = d.countryCode();
        this.websiteUrl = d.websiteUrl();
        this.taxId = d.taxId();
        this.paymentTerms = d.paymentTerms();
        this.notes = d.notes();
        this.categories.clear();
        this.categories.addAll(d.categories());
    }

    public void changeStatus(SupplierStatus next, String reason) {
        if (next == status) {
            throw new ConflictException("Supplier is already " + status);
        }
        boolean hasReason = reason != null && !reason.isBlank();
        if (next == SupplierStatus.BLOCKED && !hasReason) {
            throw new BadRequestException("A reason is required to block a supplier");
        }
        this.status = next;
        this.statusReason = next == SupplierStatus.ACTIVE || !hasReason ? null : reason.trim();
    }

    public UUID getId() { return id; }
    public String getName() { return name; }
    public String getContactName() { return contactName; }
    public String getContactEmail() { return contactEmail; }
    public String getContactPhone() { return contactPhone; }
    public String getCountryCode() { return countryCode; }
    public String getWebsiteUrl() { return websiteUrl; }
    public String getTaxId() { return taxId; }
    public String getPaymentTerms() { return paymentTerms; }
    public String getNotes() { return notes; }
    public SupplierStatus getStatus() { return status; }
    public String getStatusReason() { return statusReason; }
    public Set<String> getCategories() { return categories; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
}
