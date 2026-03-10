CREATE TABLE IF NOT EXISTS log_events (
    event_id    TEXT PRIMARY KEY,
    service     TEXT NOT NULL,
    level       TEXT NOT NULL CHECK (level IN ('DEBUG','INFO','WARN','ERROR','FATAL')),
    message     TEXT NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trace_id    TEXT,
    span_id     TEXT,
    metadata    JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_log_events_service   ON log_events(service);
CREATE INDEX IF NOT EXISTS idx_log_events_level     ON log_events(level);
CREATE INDEX IF NOT EXISTS idx_log_events_timestamp ON log_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_log_events_trace_id  ON log_events(trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_log_events_metadata  ON log_events USING GIN (metadata);
