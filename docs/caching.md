# LinkForge Caching Strategy

LinkForge heavily relies on Redis to maintain high performance and low response latency.

## 1. URL Redirection Cache

When resolving a short code to a destination URL:
* **Key**: `short_url:<short_code>`
* **Value**: `{"original_url": "...", "id": ...}`
* **Time-to-Live (TTL)**: 24 Hours (`86400` seconds)

### Invalidation Policy
Since short URL mappings are generally static (they are generated once and rarely edited), a passive expiry (TTL) is highly effective. If an edit feature is added, the cache must be cleared explicitly:
```python
cache.delete(f"short_url:{short_code}")
```

---

## 2. Dashboard Analytics Cache

Computing stats requires aggregating counts, tech profiles, and chronological traffic trends. This is a CPU-intensive operation if the `ClickEvent` table has millions of rows.
* **Key**: `dashboard_stats`
* **Value**: A serialized dictionary containing all dashboard card counters, distributions, and time-series arrays.
* **Time-to-Live (TTL)**: 5 Minutes (`300` seconds)

### Invalidation Policy
The dashboard data refreshes dynamically every 5 minutes. This reduces database queries to a maximum of 12 per hour, regardless of how many admins are viewing the dashboard simultaneously.

---

## 3. Rate Limiter Cache

To prevent resource exhaustion attacks:
* **Key**: `rate_limit:create_url:<ip_address>`
* **Value**: Integer counter.
* **TTL**: 1 Hour (`3600` seconds)
* **Strategy**: Fixed window counter incremented atomically.
```python
cache.incr(key)
```
If the cache returns a value greater than `100`, the middleware throws an immediate HTTP 429 response, avoiding hitting the Django template or database layers.
