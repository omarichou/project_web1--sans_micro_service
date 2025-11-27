# Migration to microservices (scaffold)

This workspace contains a minimal scaffold converting the original monolith into microservices for local development and testing.

Services included:
- `auth` (port 5001): register/login/users
- `dishes` (port 5002): create/list dishes
- `orders` (port 5003): create/list orders
- `gateway` (port 8000): API gateway that proxies requests to services

Quick start (PowerShell):

```powershell
docker compose build
docker compose up
```

Health checks:
- http://localhost:8000/health (gateway)
- http://localhost:5001/health (auth)
- http://localhost:5002/health (dishes)
- http://localhost:5003/health (orders)

Example flows (via gateway):
- Register user: POST http://localhost:8000/api/auth/register {"username":"u","password":"p"}
- Create dish: POST http://localhost:8000/api/dishes {"name":"Pizza","price":9.9}
- Create order: POST http://localhost:8000/api/orders {"user_id":1,"items":[{"dish_id":1,"qty":1}]}

Next recommended steps:
- Replace plain-text passwords with hashed passwords and JWT auth.
- Move to dedicated databases (Postgres) per service and add migrations.
- Add service discovery, retries and circuit breakers for production.
