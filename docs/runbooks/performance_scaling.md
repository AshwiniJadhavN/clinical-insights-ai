# Performance & Scaling Runbook

Clinical Insights AI is designed for demonstration and small-scale clinical deployments. This runbook covers monitoring, scaling, and debugging under load.

---

## 1. Performance Metrics

### Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Query latency (p95) | <2s (local), <3s (production) | >5s |
| Document upload latency | <5s | >15s |
| Vector retrieval latency | <500ms | >1s |
| API error rate | <0.1% | >1% |
| Database connection pool utilization | <70% | >90% |
| Memory usage | <500MB | >800MB |
| CPU usage | <50% | >80% |

### Prometheus Metrics

The application exposes metrics at `/metrics` (Prometheus format):

```
clinical_insights_http_requests_total — Total HTTP requests handled
clinical_insights_indexed_chunks — Current count of indexed chunks
clinical_insights_app_info{version=...} — Application version info
```

Access via:
```bash
curl http://localhost:8000/metrics
```

---

## 2. Bottleneck Analysis

### Common Bottlenecks (in order of impact)

#### 1. Embedding Generation (50-70% of latency)
- Happens during document upload and query
- Single-threaded by default (sentence-transformers)
- **Fix:** Batch embedding requests, consider GPU acceleration

#### 2. Vector Retrieval (20-30% of latency)
- ChromaDB (default) — in-memory, fast but limited to single node
- PGVector — network latency + database query
- **Fix:** Pre-warm vector cache, use similarity pruning

#### 3. LLM Generation (10-20% of latency)
- Network call to upstream provider (OpenAI, etc.)
- Timeout risk during peak load
- **Fix:** Implement request timeout, cache common queries

#### 4. Database Operations (5-10% of latency)
- Audit trail writes, document metadata
- Connection pool exhaustion under high concurrency
- **Fix:** Async audit writes, increase connection pool

---

## 3. Scaling Strategies

### Vertical Scaling (Single Node)

**CPU/Memory:**
```bash
# Monitor current usage
docker stats clinical-insights-ai-api

# Increase resources in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 2G
```

**Database:**
```bash
# Increase PostgreSQL connection pool in config
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

**Embedding Model:**
```bash
# Use faster model (tradeoff: slightly lower quality)
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fast
EMBEDDING_MODEL=all-mpnet-base-v2  # Slower but higher quality
```

### Horizontal Scaling (Multiple Nodes)

**Kubernetes Deployment:**
```yaml
# See k8s/deployment.yaml
replicas: 3  # Start with 3 instances
resources:
  requests:
    memory: "500Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

**Load Balancing:**
- Use Kubernetes service for automatic load balancing
- Or use HAProxy/nginx in front of multiple instances

**Vector Store Considerations:**
- **ChromaDB (default):** Each instance has its own in-memory copy — stale reads across instances
  - **Solution:** Deploy shared PostgreSQL + PGVector (see below)
- **PGVector:** Shared PostgreSQL backend — all instances read/write same index
  - More network latency but guarantees consistency

**Switch to PGVector:**
```bash
docker-compose.yml: Set VECTOR_BACKEND=pgvector
# PostgreSQL already included in compose
```

---

## 4. Load Testing

### Quick Load Test (Local)

```bash
# Using Apache Bench (ab)
ab -n 100 -c 10 http://localhost:8000/health

# Using wrk
wrk -t4 -c100 -d30s http://localhost:8000/health

# Using k6 (JavaScript-based)
cat > load_test.js <<EOF
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '60s', target: 50 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  let res = http.get('http://localhost:8000/docs');
  check(res, { 'status was 200': (r) => r.status == 200 });
}
EOF
k6 run load_test.js
```

### Production Load Test

1. **Warm up** the system (index documents, pre-populate cache)
2. **Baseline** — measure current performance under normal traffic
3. **Ramp up** — gradually increase load to peak expected usage
4. **Sustain** — hold peak load for 5+ minutes
5. **Measure** — p95, p99 latency, error rate, resource usage

**Example k6 script for query load:**
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 10 },  // Warm up
    { duration: '5m', target: 50 },  // Ramp to peak
    { duration: '5m', target: 50 },  // Sustain
    { duration: '1m', target: 0 },   // Cool down
  ],
};

export default function () {
  let res = http.post('http://localhost:8000/query', 
    JSON.stringify({ question: 'What is the patient potassium level?' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(res, {
    'status is 200': (r) => r.status == 200,
    'latency < 3s': (r) => r.timings.duration < 3000,
  });
  sleep(1);
}
```

---

## 5. Debugging Under Load

### Real-Time Monitoring

```bash
# 1. Watch container metrics
docker stats clinical-insights-ai-api

# 2. Stream application logs
docker logs -f clinical-insights-ai-api

# 3. Check metrics endpoint
watch -n 1 'curl -s http://localhost:8000/metrics | grep clinical_insights'

# 4. Monitor database connections
docker exec clinical-insights-ai-db psql -U clinical -d clinical_insights \
  -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

### Slow Query Analysis

1. **Enable query logging** in PostgreSQL:
```sql
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();
```

2. **Check logs:**
```bash
docker exec clinical-insights-ai-db tail -f /var/log/postgresql/postgresql.log
```

3. **Analyze query plans:**
```sql
EXPLAIN ANALYZE SELECT * FROM documents WHERE id = 'xyz';
```

### Memory Leaks

```bash
# Check memory trend over time
docker stats --no-stream clinical-insights-ai-api | head -1
sleep 300
docker stats --no-stream clinical-insights-ai-api | tail -1
# If memory grows significantly, investigate connection/cache leaks

# Python memory profiling
pip install memory_profiler
python -m memory_profiler backend/main.py
```

### Latency Profiling

```bash
# Add performance tracing (already in place via observability/metrics.py)
# Check backend logs for slow operations:
docker logs clinical-insights-ai-api | grep -i "slow\|latency"
```

---

## 6. Common Issues & Fixes

| Issue | Symptom | Solution |
|-------|---------|----------|
| Vector store out of memory | OOM error, pod eviction | Use PGVector + PostgreSQL instead of ChromaDB |
| Database connection exhaustion | "too many connections" error | Increase pool size, enable connection pooling, use pgBouncer |
| Embedding queue buildup | Query latency spikes | Use faster embedding model, batch embeddings |
| LLM timeout | 502 errors | Increase timeout, use smaller context windows |
| Retrieval latency spike | Slow vector search | Add vector index, increase cache size |
| Audit log bloat | Slow writes, disk full | Archive old logs, implement log rotation |

---

## 7. Capacity Planning

### Rule of Thumb (Single Instance)

- **Documents:** Up to 10,000 documents (~100MB index)
- **Concurrent users:** Up to 10 simultaneous queries
- **Query latency:** 1-3 seconds at p95
- **Uptime requirement:** 99.9% (production) — use multi-instance + failover

### Multi-Instance (3+ replicas)

- **Documents:** Up to 100,000 documents (share via PGVector)
- **Concurrent users:** Up to 100 simultaneous queries
- **Query latency:** <2s at p95 with load balancing
- **Uptime requirement:** 99.99% (with proper redundancy)

### Estimate Resource Needs

```
Per 1,000 documents:
- Embedding storage: ~10MB (384-dim vectors)
- Metadata storage: ~5MB (PostgreSQL)
- Memory (runtime): +50MB (vector cache)

Per 10 QPS (queries per second):
- CPU: +0.5 core
- Memory: +200MB (request buffer + LLM context)
- Database connections: +5 (pool overhead)
```

---

## 8. Production Readiness Checklist

Before scaling to production:

- [ ] Implement centralized immutable audit logging (not JSONL files)
- [ ] Add HIPAA security controls (encryption, access logging)
- [ ] Set up monitoring dashboard (Grafana + Prometheus)
- [ ] Configure alerting (PagerDuty, Slack)
- [ ] Test disaster recovery (database failover, backup restore)
- [ ] Load test to 2x expected peak traffic
- [ ] Document runbook for on-call team
- [ ] Establish SLO (Service Level Objective) — e.g., 99.5% uptime
- [ ] Set up incident response process
- [ ] Get clinical validation and FDA approval (if applicable)

---

## 9. Contacts & Escalation

For performance issues:

1. **Check:** `docker stats`, `/metrics`, logs
2. **Scale:** Adjust Docker resources or increase replicas
3. **Investigate:** Profile slow operations, check database
4. **Escalate:** Contact infrastructure/platform team if needed

---

## References

- Prometheus metrics: `backend/observability/metrics.py`
- Health probes: `k8s/deployment.yaml`
- Docker Compose: `docker-compose.yml`
- Configuration: `backend/config.py`
