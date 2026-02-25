// k6 load test for global log platform
// Usage: k6 run --vus 50 --duration 60s k6-global-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

const ingestionErrors = new Counter('ingestion_errors');
const ingestionSuccess = new Rate('ingestion_success_rate');
const ingestionLatency = new Trend('ingestion_latency_ms', true);

const ENDPOINTS = [
  __ENV.US_EAST_ENDPOINT || 'http://localhost:8000',
  __ENV.EU_WEST_ENDPOINT || 'http://localhost:8001',
];

const SERVICES = ['auth','api-gateway','orders','payments','inventory'];
const LEVELS   = ['INFO','INFO','INFO','WARN','ERROR'];

export const options = {
  stages: [
    { duration: '10s', target: 10  },
    { duration: '30s', target: 50  },
    { duration: '10s', target: 100 },
    { duration: '30s', target: 100 },
    { duration: '10s', target: 0   },
  ],
  thresholds: {
    ingestion_success_rate: ['rate>0.99'],
    ingestion_latency_ms:   ['p(99)<500'],
    http_req_duration:      ['p(95)<300'],
  },
};

export default function () {
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
  const payload  = JSON.stringify({
    service:   SERVICES[Math.floor(Math.random() * SERVICES.length)],
    level:     LEVELS[Math.floor(Math.random() * LEVELS.length)],
    message:   `Request completed in ${Math.floor(Math.random() * 500)}ms`,
    timestamp: Date.now() / 1000,
    trace_id:  `${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`,
  });

  const start    = Date.now();
  const response = http.post(`${endpoint}/ingest`, payload, {
    headers: { 'Content-Type': 'application/json' },
    timeout: '5s',
  });
  ingestionLatency.add(Date.now() - start);

  const ok = check(response, {
    'status 202': (r) => r.status === 202,
  });
  if (!ok) ingestionErrors.add(1);
  ingestionSuccess.add(ok ? 1 : 0);

  sleep(Math.random() * 0.2);
}
