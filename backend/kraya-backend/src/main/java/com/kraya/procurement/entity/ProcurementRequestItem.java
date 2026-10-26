package com.kraya.procurement.entity;

import jakarta.persistence.*;

import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "procurement_request_items")
public class ProcurementRequestItem {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "request_id", nullable = false, updatable = false)
    private ProcurementRequest request;

    @Column(name = "line_no", nullable = false)
    private int lineNo;

    @Column(nullable = false, length = 255)
    private String name;

    @Column(length = 2000)
    private String description;

    @Column(nullable = false, precision = 14, scale = 3)
    private BigDecimal quantity;

    @Column(nullable = false, length = 30)
    private String unit;

    protected ProcurementRequestItem() {
    }

    ProcurementRequestItem(ProcurementRequest request, int lineNo, String name, String description,
                           BigDecimal quantity, String unit) {
        this.request = request;
        this.lineNo = lineNo;
        this.name = name;
        this.description = description;
        this.quantity = quantity;
        this.unit = unit;
    }

    public UUID getId() { return id; }
    public int getLineNo() { return lineNo; }
    public String getName() { return name; }
    public String getDescription() { return description; }
    public BigDecimal getQuantity() { return quantity; }
    public String getUnit() { return unit; }
}
