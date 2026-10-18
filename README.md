# Order Service

A small order-processing API with the moving parts of a real backend:

| Part | What it does |
|---|---|
| Postgres (`DATABASE_URL`) | Orders |
| MySQL (`LEGACY_DB_URL`) | Legacy billing database: customer credit limits |
| MongoDB (`MONGODB_URI`) | Audit log of every order event |
| Redis (`REDIS_URL`) | Product price cache and per-client rate limit |
| RabbitMQ (`AMQP_URL`) | `order.created` events |
| Worker (`python -m app.worker`) | Confirms new orders and audits them |

Run it: `docker compose up`. API on port 8080: `python main.py`. Tests: `pytest`.

## API

- `GET /health`
- `POST /customers/{id}/credit` `{"credit_limit": 500}` / `GET /customers/{id}/credit`
- `POST /orders` `{"customer_id": 1, "product": "mouse", "quantity": 2}`: 201, 400 (bad input or unknown product), 402 (over credit), 404 (unknown customer)
- `GET /orders/{id}`, `GET /orders?customer_id=1`, `GET /orders/{id}/audit`
