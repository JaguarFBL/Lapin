-- Examples for the IA/backend

-- 1. Get primary adult rabbit requirements
SELECT *
FROM v_primary_adult_requirements
ORDER BY category, nutrient_id, unit;

-- 2. Get chemical thresholds for commercial uniform pellets
SELECT nutrient_id, min_value, target_value, max_value, unit, basis, source_id
FROM v_product_thresholds
WHERE basis = 'commercial_uniform_pellet'
ORDER BY nutrient_id;

-- 3. Get practical ration rules
SELECT nutrient_id, min_value, target_value, max_value, unit, basis, source_id
FROM v_practical_ration
ORDER BY nutrient_id, source_id;

-- 4. Get alfalfa hay ingredient composition
SELECT ingredient_name_en, nutrient_id, avg_value, sd, min_value, max_value, unit, basis
FROM ingredient_compositions
WHERE ingredient_id = 'alfalfa_hay'
ORDER BY nutrient_id;
