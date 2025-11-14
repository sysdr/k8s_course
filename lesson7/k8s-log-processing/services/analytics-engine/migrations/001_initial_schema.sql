-- Log metrics aggregation table
CREATE TABLE IF NOT EXISTS log_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    service VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(timestamp, service, level)
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_log_metrics_timestamp ON log_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_log_metrics_service ON log_metrics(service);
CREATE INDEX IF NOT EXISTS idx_log_metrics_level ON log_metrics(level);

-- Raw logs table (optional, for detailed storage)
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    level VARCHAR(20) NOT NULL,
    service VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_service_level ON logs(service, level);
