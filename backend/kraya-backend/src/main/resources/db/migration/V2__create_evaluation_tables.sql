CREATE TABLE evaluation_records (
    id VARCHAR(36) PRIMARY KEY,
    supplier_id VARCHAR(64) NOT NULL,
    quote_id VARCHAR(64) NOT NULL,
    final_score NUMERIC(5, 2) NOT NULL,
    baseline_score NUMERIC(5, 2) NOT NULL,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shap_attributions (
    id BIGSERIAL PRIMARY KEY,
    evaluation_id VARCHAR(36) REFERENCES evaluation_records(id) ON DELETE CASCADE,
    feature_name VARCHAR(64) NOT NULL,
    display_label VARCHAR(128) NOT NULL,
    feature_value VARCHAR(64) NOT NULL,
    shap_value NUMERIC(8, 4) NOT NULL,
    score_delta NUMERIC(6, 2) NOT NULL,
    is_positive BOOLEAN NOT NULL
);