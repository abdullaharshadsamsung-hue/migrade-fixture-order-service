"""Order Service: orders in Postgres, credit limits in a legacy MySQL
database, an audit log in MongoDB, a Redis cache and rate limit, and
order events through RabbitMQ to a background worker."""

from flask import Flask


def create_app() -> Flask:
    from app.db import init_db
    from app.routes import api

    init_db()
    app = Flask(__name__)
    app.register_blueprint(api)
    return app
