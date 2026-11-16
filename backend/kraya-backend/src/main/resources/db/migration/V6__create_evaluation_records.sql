
CREATE TABLE evaluation_records (
    id UUID PRIMARY KEY,
    supplier_id UUID NOT NULL,
    quote_id UUID NOT NULL,
    composite_score DOUBLE PRECISION NOT NULL,
    baseline_score DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_evaluation_supplier
    ON evaluation_records(supplier_id);

CREATE INDEX idx_evaluation_quote
    ON evaluation_records(quote_id);
