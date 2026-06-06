# Rabbit Nutrition DB

Version: rabbit_requirements_2026_1_extraction_v1
Created: 2026-06-06

## Scope

Species: rabbit
Profile: rabbit_adult_maintenance

This package contains structured numeric nutrition data extracted only from the project-documented sources:
- FEDIAF 2024
- Merck Veterinary Manual 2024
- CHUV Universite de Montreal 2025
- NCSU Veterinary Hospital
- Feedipedia / INRAE-CIRAD-AFZ alfalfa hay

## Files

- rabbit_knowledge_pack.json: AI-friendly full knowledge pack.
- rabbit_knowledge_pack.schema.json: minimal JSON Schema.
- nutrient_requirements.jsonl: one requirement per line.
- rabbit_nutrition_seed.sql: SQL schema + inserts.
- rabbit_nutrition.sqlite: ready-to-open SQLite database with views.
- CSV files: table exports for quick import or manual review.
- rabbit_nutrition_tables.xlsx: human-readable workbook.

## Important usage rules

1. Prefer FEDIAF rows with priority=primary for nutrient scoring.
2. Do not compare values unless unit and basis are compatible.
3. Feedipedia alfalfa data is ingredient composition, not a rabbit requirement.
4. review_status=extracted_from_source means structured extraction, not veterinary sign-off.
5. Use product_threshold rows only for products matching the stated basis, especially commercial_uniform_pellet.

## Intégration Rabbit Scan (IA)

Ce dossier sert de *Knowledge Pack* (Base de connaissances vétérinaire) pour les LLM (ex: Gemini) dans le backend Rabbit Scan.
- **`clinical_rules.json`** : Fichier ajouté spécifiquement pour piloter le raisonnement de l'agent Comparateur. Il contient les règles d'ajustement dynamique des seuils nutritionnels selon les pathologies du lapin (ex: calculs urinaires = réduction du calcium_max).
- **Injection RAG** : Ces fichiers bruts (CSV, JSON) sont directement injectés dans le contexte du modèle, ce qui garantit une recommandation sourcée et sans hallucination.
