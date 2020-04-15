SELECT
    p_city.entity_id AS city_id,
    p_city.name,
    ST_x(p_city.point) AS longitude,
    ST_y(p_city.point) AS latitude,
    p_country.entity_id AS country_id
FROM polygons AS p_city
JOIN category_hierarchy AS ch
ON p_city.entity_id = ch.child_id
JOIN polygons AS p_country
ON p_country.entity_id = ch.parent_id
WHERE p_city.category_type_id = 5 AND p_city.point IS NOT NULL
AND p_country.category_type_id = 2