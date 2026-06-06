# Rabbit product database v1

This package builds the product side of the rabbit/NAC scoring app.
It is designed to be compared against the provided rabbit requirements pack.

## Files

- complete_postgres_schema_and_seed.sql: full PostgreSQL/Supabase schema plus seed data.
- 01_product_schema_postgres.sql: schema only.
- 02_seed_requirements_and_demo_products.sql: seed requirements and two demo rabbit pellet products.
- product_ingestion_contract.json: source priority, mapping rules, API endpoints and confidence policy.
- fetch_openpetfoodfacts_example.py: minimal barcode fetch scaffold.
- compare_product_to_thresholds.py: deterministic comparison helper.
- rabbit_product_demo.sqlite: local SQLite demo database.

## Demo products included

- Oxbow Essentials Adult Rabbit Food
- Burgess Excel Adult Rabbit Nuggets with Mint

## Important rule

Do not score a product only because a barcode database found a name.
Score only when analytical constituents are available and mapped to canonical nutrients.

## Import in Supabase

1. Open Supabase SQL Editor.
2. Run complete_postgres_schema_and_seed.sql.
3. Query v_rabbit_pellet_product_comparison.
4. Connect your API to product_source_registry and product_fetch_jobs.

## V1 product lookup order

1. OpenPetFoodFacts
2. OpenFoodFacts universal scan with product_type=all
3. Manufacturer official page
4. Retailer product page
5. User OCR

Generated at 2026-06-06T10:10:44.
