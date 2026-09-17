-- PostgreSQL / Amazon Aurora Relational Variant Schema
-- Supports high-performance point lookups and clinical metadata correlation

CREATE TABLE IF NOT EXISTS variants (
    id BIGSERIAL PRIMARY KEY,
    start BIGINT NOT NULL,
    end_pos BIGINT NOT NULL,
    reference_name VARCHAR(32) NOT NULL,
    reference_bases VARCHAR(255) NOT NULL,
    alternate_bases VARCHAR(255) NOT NULL,
    sample_id VARCHAR(64) NOT NULL,
    genotype VARCHAR(16) NOT NULL,
    qual DOUBLE PRECISION,
    filter VARCHAR(32),
    dp INT,
    gq INT,
    allele_depth VARCHAR(64),
    attributes JSONB,
    cohort_id VARCHAR(64),
    engine VARCHAR(64) DEFAULT 'aurora_postgres'
);

-- Index on engine for multi-tenant / multi-engine filtering
CREATE INDEX IF NOT EXISTS idx_variants_engine
ON variants (engine);

-- B-Tree index for locus range queries and carrier lookups
CREATE INDEX IF NOT EXISTS idx_variants_locus 
ON variants (reference_name, start);

-- B-Tree index for sample-level retrieval
CREATE INDEX IF NOT EXISTS idx_variants_sample 
ON variants (sample_id);

-- GIN index for JSONB attribute filtering (e.g. gene symbol or clinical significance)
CREATE INDEX IF NOT EXISTS idx_variants_attributes_gin 
ON variants USING GIN (attributes);
