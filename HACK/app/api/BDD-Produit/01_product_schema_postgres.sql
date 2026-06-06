-- Rabbit product database v1
-- Target: PostgreSQL / Supabase
-- Purpose: store pet/NAC product labels, source evidence, normalized nutrients and comparisons.

CREATE TABLE IF NOT EXISTS species (
    id TEXT PRIMARY KEY,
    common_name_fr TEXT,
    common_name_en TEXT,
    scientific_name TEXT
);

CREATE TABLE IF NOT EXISTS animal_profiles (
    id TEXT PRIMARY KEY,
    species_id TEXT NOT NULL REFERENCES species(id),
    life_stage TEXT NOT NULL,
    physiological_status TEXT NOT NULL,
    label_fr TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS nutrients (
    id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    display_name_fr TEXT,
    category TEXT NOT NULL,
    synonyms JSONB DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS nutrient_requirements (
    id TEXT PRIMARY KEY,
    species_id TEXT NOT NULL REFERENCES species(id),
    animal_profile_id TEXT NOT NULL REFERENCES animal_profiles(id),
    nutrient_id TEXT NOT NULL REFERENCES nutrients(id),
    requirement_type TEXT NOT NULL,
    min_value NUMERIC,
    target_value NUMERIC,
    max_value NUMERIC,
    unit TEXT NOT NULL,
    basis TEXT NOT NULL,
    source_id TEXT,
    source_metric TEXT,
    confidence_level TEXT NOT NULL,
    review_status TEXT NOT NULL,
    priority TEXT NOT NULL,
    version TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS product_source_registry (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT,
    access_model TEXT NOT NULL,
    reliability_level TEXT NOT NULL,
    priority_order INTEGER NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    barcode TEXT UNIQUE,
    brand TEXT,
    name TEXT NOT NULL,
    product_type TEXT NOT NULL,
    target_species JSONB DEFAULT '[]'::jsonb,
    life_stage JSONB DEFAULT '[]'::jsonb,
    data_quality_score NUMERIC,
    primary_source_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_source_records (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id),
    registry_source_id TEXT NOT NULL REFERENCES product_source_registry(id),
    source_name TEXT NOT NULL,
    source_url TEXT,
    source_product_id TEXT,
    fetched_at TIMESTAMPTZ,
    raw_payload JSONB DEFAULT '{}'::jsonb,
    reliability_level TEXT NOT NULL,
    license_notes TEXT
);

ALTER TABLE products
    ADD CONSTRAINT products_primary_source_fk
    FOREIGN KEY (primary_source_id) REFERENCES product_source_records(id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE IF NOT EXISTS product_ingredients (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id),
    ingredients_text TEXT NOT NULL,
    source_record_id TEXT NOT NULL REFERENCES product_source_records(id),
    extraction_method TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_images (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id),
    image_type TEXT NOT NULL,
    image_url TEXT,
    local_path TEXT,
    source_record_id TEXT REFERENCES product_source_records(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_nutrients (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id),
    nutrient_id TEXT REFERENCES nutrients(id),
    source_metric TEXT NOT NULL,
    declared_text TEXT NOT NULL,
    value_min NUMERIC,
    value_max NUMERIC,
    value_exact NUMERIC,
    declared_unit TEXT NOT NULL,
    declared_basis TEXT NOT NULL,
    value_type TEXT NOT NULL CHECK (value_type IN ('exact','min','max','range','unmapped_exact','unknown')),
    normalized_value_min NUMERIC,
    normalized_value_max NUMERIC,
    normalized_value_exact NUMERIC,
    normalized_unit TEXT,
    normalized_basis TEXT,
    source_record_id TEXT NOT NULL REFERENCES product_source_records(id),
    extraction_method TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    canonicalization_status TEXT NOT NULL DEFAULT 'mapped',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_fetch_jobs (
    id TEXT PRIMARY KEY,
    barcode TEXT,
    product_id TEXT REFERENCES products(id),
    requested_source_id TEXT REFERENCES product_source_registry(id),
    status TEXT NOT NULL CHECK (status IN ('queued','fetched','not_found','failed','needs_ocr','needs_review')),
    request_url TEXT,
    response_status INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS product_nutrient_candidates (
    id TEXT PRIMARY KEY,
    product_id TEXT REFERENCES products(id),
    source_record_id TEXT REFERENCES product_source_records(id),
    raw_text TEXT NOT NULL,
    proposed_nutrient_id TEXT REFERENCES nutrients(id),
    proposed_value_min NUMERIC,
    proposed_value_max NUMERIC,
    proposed_value_exact NUMERIC,
    proposed_unit TEXT,
    proposed_basis TEXT,
    ai_confidence NUMERIC,
    status TEXT NOT NULL CHECK (status IN ('pending_review','validated','rejected','conflicting')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_score_runs (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id),
    species_id TEXT NOT NULL REFERENCES species(id),
    animal_profile_id TEXT NOT NULL REFERENCES animal_profiles(id),
    score_version TEXT NOT NULL,
    total_score NUMERIC,
    grade TEXT,
    details JSONB NOT NULL,
    calculated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_product_nutrients_product ON product_nutrients(product_id);
CREATE INDEX IF NOT EXISTS idx_product_nutrients_nutrient ON product_nutrients(nutrient_id);
CREATE INDEX IF NOT EXISTS idx_requirements_profile_type ON nutrient_requirements(animal_profile_id, requirement_type, basis);

CREATE OR REPLACE VIEW v_product_thresholds AS
SELECT *
FROM nutrient_requirements
WHERE species_id = 'rabbit'
  AND animal_profile_id = 'rabbit_adult_maintenance'
  AND requirement_type = 'product_threshold'
  AND basis = 'commercial_uniform_pellet';

CREATE OR REPLACE VIEW v_product_latest_nutrients AS
SELECT
    pn.*,
    p.brand,
    p.name,
    p.product_type
FROM product_nutrients pn
JOIN products p ON p.id = pn.product_id;

CREATE OR REPLACE VIEW v_rabbit_pellet_product_comparison AS
SELECT
    p.id AS product_id,
    p.brand,
    p.name,
    pn.nutrient_id,
    pn.declared_text,
    pn.value_type,
    COALESCE(pn.value_exact, pn.value_min) AS product_lower_value,
    COALESCE(pn.value_exact, pn.value_max) AS product_upper_value,
    pn.declared_unit,
    t.min_value AS threshold_min,
    t.max_value AS threshold_max,
    t.unit AS threshold_unit,
    t.basis AS threshold_basis,
    CASE
        WHEN pn.nutrient_id IS NULL THEN 'unmapped'
        WHEN pn.declared_unit <> t.unit THEN 'unit_mismatch'
        WHEN t.min_value IS NOT NULL AND COALESCE(pn.value_exact, pn.value_min) IS NULL THEN 'missing_lower_bound'
        WHEN t.max_value IS NOT NULL AND COALESCE(pn.value_exact, pn.value_max) IS NULL THEN 'cannot_confirm_upper_bound'
        WHEN t.min_value IS NOT NULL AND COALESCE(pn.value_exact, pn.value_min) < t.min_value THEN 'below_min'
        WHEN t.max_value IS NOT NULL AND COALESCE(pn.value_exact, pn.value_max) > t.max_value THEN 'above_max'
        ELSE 'ok'
    END AS comparison_status
FROM products p
JOIN product_nutrients pn ON pn.product_id = p.id
JOIN v_product_thresholds t ON t.nutrient_id = pn.nutrient_id
WHERE p.product_type = 'commercial_uniform_pellet';
