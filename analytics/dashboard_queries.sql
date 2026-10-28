-- Query 1: QA outcomes by feed run.
SELECT f.run_started_at, f.source_name,
       COUNT(v.rule_id) AS rules_checked,
       SUM(CASE WHEN v.status = 'FAIL' THEN 1 ELSE 0 END) AS failed_rules,
       SUM(COALESCE(v.affected_records, 0)) AS affected_records
FROM feed_run f LEFT JOIN validation_result v ON f.run_id=v.run_id
GROUP BY f.run_id, f.run_started_at, f.source_name
ORDER BY f.run_started_at;

-- Query 2: walk vs wait recommendations by route; not equivalent to rider adoption.
SELECT route_id, action, COUNT(*) AS recommendations,
       ROUND(AVG(walking_minutes),2) AS mean_walk_minutes,
       SUM(CASE WHEN action='WALK' THEN expected_steps ELSE 0 END) AS potential_steps
FROM recommendation_event
GROUP BY route_id, action
ORDER BY recommendations DESC;

-- Query 3: observed catch rates ONLY on events with confirmed observation.
SELECT route_id, action, COUNT(*) AS verified_outcomes,
       ROUND(AVG(CAST(caught_vehicle AS REAL)),3) AS verified_catch_rate
FROM recommendation_event
WHERE arrival_observed=1 AND caught_vehicle IS NOT NULL
GROUP BY route_id, action
HAVING COUNT(*) >= 10;
