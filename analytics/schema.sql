-- CommuteIQ SQLite analytics schema (v1)
-- Run on a new local DB. Demo records are always labelled DEMO.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS feed_run (
  run_id INTEGER PRIMARY KEY,
  run_started_at TEXT NOT NULL,
  source_name TEXT NOT NULL,
  data_origin TEXT NOT NULL CHECK(data_origin IN ('DEMO','LIVE')),
  records_loaded INTEGER NOT NULL DEFAULT 0 CHECK(records_loaded >= 0)
);
CREATE TABLE IF NOT EXISTS validation_result (
  run_id INTEGER NOT NULL REFERENCES feed_run(run_id),
  rule_id TEXT NOT NULL,
  severity TEXT,
  status TEXT NOT NULL CHECK(status IN ('PASS','FAIL','SKIP')),
  affected_records INTEGER NOT NULL DEFAULT 0 CHECK(affected_records >= 0),
  PRIMARY KEY (run_id, rule_id)
);
CREATE TABLE IF NOT EXISTS recommendation_event (
  event_id INTEGER PRIMARY KEY,
  observed_at TEXT NOT NULL,
  route_id TEXT NOT NULL,
  current_stop_id TEXT NOT NULL,
  next_stop_id TEXT NOT NULL,
  walking_minutes REAL NOT NULL CHECK(walking_minutes >= 0),
  current_eta_minutes REAL,
  next_eta_minutes REAL,
  feed_age_seconds REAL,
  action TEXT NOT NULL CHECK(action IN ('WALK','WAIT')),
  decision_reason TEXT NOT NULL,
  expected_steps INTEGER NOT NULL DEFAULT 0 CHECK(expected_steps >= 0),
  data_origin TEXT NOT NULL CHECK(data_origin IN ('DEMO','LIVE')),
  -- Outcomes NULL unless independently verified. A suggestion is NOT a completed walk.
  caught_vehicle INTEGER CHECK(caught_vehicle IN (0,1)),
  arrival_observed INTEGER NOT NULL DEFAULT 0 CHECK(arrival_observed IN (0,1)),
  CHECK(arrival_observed = 1 OR caught_vehicle IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_rec_route_time ON recommendation_event(route_id, observed_at);
