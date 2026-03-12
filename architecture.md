**Scaling Notes (in architecture.md):**
- 10k+ req/sec: Replace SQLite with Postgres + add Celery queue + Redis cache  
- Horizontal scaling: Deploy multiple instances behind load balancer  
