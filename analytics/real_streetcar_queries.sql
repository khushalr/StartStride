-- StopStride SQL analysis over real TTC streetcar delay records (2025+).
-- After the Python ETL creates outputs/real/streetcar.sqlite, run using sqlite3.
-- Incident records are NOT unique riders, vehicle trips, or a denominator for reliability.
-- Data originates in the City of Toronto TTC Streetcar Delay Data dataset.

-- 1. Route incident burden: absolute logged events, NOT failure rates.
WITH route_counts AS (
    SELECT route, COUNT(*) AS incident_count,
           SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) AS positive_incidents,
           ROUND(AVG(delay_minutes),2) AS mean_delay_minutes
    FROM streetcar_incident
    GROUP BY route
)
SELECT route, incident_count, positive_incidents, mean_delay_minutes,
       DENSE_RANK() OVER (ORDER BY incident_count DESC) AS recorded_incident_rank
FROM route_counts
ORDER BY incident_count DESC;

-- 2. Monthly trends: zero-minute records retained in event count.
SELECT strftime('%Y-%m', record_date) AS month,
       COUNT(*) AS events,
       SUM(CASE WHEN delay_minutes = 0 THEN 1 ELSE 0 END) AS zero_minute_events,
       SUM(delay_minutes) AS recorded_delay_minutes
FROM streetcar_incident
GROUP BY strftime('%Y-%m', record_date)
ORDER BY month;

-- 3. Intraday distribution by route, including positive-delay share.
SELECT route, hour, COUNT(*) AS records,
       SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END) AS positive_records,
       ROUND(100.0 * SUM(CASE WHEN delay_minutes > 0 THEN 1 ELSE 0 END)
             / NULLIF(COUNT(*),0), 2) AS positive_share_of_logged_records_pct
FROM streetcar_incident
GROUP BY route, hour
ORDER BY route, hour;

-- 4. Volume and data range: these are observed logs, not a prediction system.
SELECT COUNT(*) AS validated_records,
       COUNT(DISTINCT route) AS distinct_routes,
       MIN(record_date) AS first_record,
       MAX(record_date) AS last_record
FROM streetcar_incident;
