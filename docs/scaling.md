# LinkForge Scaling Strategy

To handle high read traffic and spikes in link creations, LinkForge follows a multi-tiered scaling strategy.

## 1. Database Optimizations

### Smart Indexing
We define database indexes on frequently queried fields:
* `ShortURL.short_code` (Unique, B-Tree): Ensures redirections run in $O(\log N)$ or index-only scans.
* `ShortURL.created_at`: For dashboard sorting.
* `ClickEvent.clicked_at`: Optimizes date-based dashboard aggregation scans.
* `ClickEvent(short_url, clicked_at)` (Compound): Optimizes charts querying click trends for individual links.

### No N+1 Queries
* In the dashboard and analytics panels, we query distributions using `.values().annotate(Count('id'))`. This groups rows in database memory in a single scan rather than performing multiple round-trip queries.
* We select related items using Django's `select_related()` (for ForeignKey/OneToOne relations) or `prefetch_related()` (for ManyToMany relations) if we load details of linked models.

---

## 2. Decoupled Processing (Celery Workers)

Redirections must be sub-millisecond. We decouple analytical logging:
* **Redirection thread**: Fetches the original URL from Redis (cache hit) and returns `HTTP 301` instantly.
* **Analytics thread**: The logging task is queued in Redis. Workers process the queue asynchronously.
* If a post goes viral, the influx of redirect requests does not saturate PostgreSQL database connections, as the writes are queued and handled by independent, auto-scaling Celery workers.

---

## 3. Redis Rate Limiting

We implement sliding fixed-window rate limiting on URL creation:
* Creates are limited (e.g. 100/hr) per IP.
* By storing rate counters in Redis memory with automatic expiries, we prevent abusive bots from flooding PostgreSQL with insert statements, protecting database CPU.

---

## 4. Horizontal Expansion (Production)
* **Web Services**: The stateless Django web container can be scaled horizontally (multiple Gunicorn pods behind a load balancer like Nginx, Cloudflare, or Render's native proxy).
* **Read-Heavy Caching**: Up to 99% of redirects can be resolved directly by the Redis cache cluster without contacting PostgreSQL.
* **Database Read Replicas**: If dashboard queries grow heavy, the primary database can stream to read replicas, and Django can route all analytical/dashboard queries to the read replicas using a custom Django database router.
