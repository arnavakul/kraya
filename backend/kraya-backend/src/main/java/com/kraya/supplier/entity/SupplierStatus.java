package com.kraya.supplier.entity;

public enum SupplierStatus {
    ACTIVE,     // can receive RFQs
    INACTIVE,   // paused, kept for history
    BLOCKED     // must not be used; a reason is required
}
