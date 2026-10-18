"""The HTTP API."""

from decimal import Decimal

from flask import Blueprint, jsonify, request

from app import audit, catalog, events
from app.db import LegacySession, Session
from app.models import CustomerCredit, Order

api = Blueprint("api", __name__)


@api.before_request
def rate_limit():
    if request.path != "/health" and not catalog.allow_request(request.remote_addr or "?"):
        return jsonify({"error": "rate limit exceeded"}), 429
    return None


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.post("/customers/<int:customer_id>/credit")
def set_credit(customer_id: int):
    body = request.get_json(silent=True) or {}
    limit = body.get("credit_limit")
    if not isinstance(limit, (int, float)) or limit < 0:
        return jsonify({"error": "credit_limit must be a non-negative number"}), 400
    with LegacySession() as db:
        credit = db.get(CustomerCredit, customer_id) or CustomerCredit(
            customer_id=customer_id, used=0
        )
        credit.credit_limit = limit
        db.add(credit)
        db.commit()
        return jsonify(
            {
                "customer_id": customer_id,
                "credit_limit": float(credit.credit_limit),
                "used": float(credit.used),
            }
        ), 200


@api.get("/customers/<int:customer_id>/credit")
def get_credit(customer_id: int):
    with LegacySession() as db:
        credit = db.get(CustomerCredit, customer_id)
        if credit is None:
            return jsonify({"error": "customer not found"}), 404
        return jsonify(
            {
                "customer_id": customer_id,
                "credit_limit": float(credit.credit_limit),
                "used": float(credit.used),
            }
        )


@api.post("/orders")
def create_order():
    body = request.get_json(silent=True) or {}
    customer_id = body.get("customer_id")
    product = body.get("product")
    quantity = body.get("quantity", 1)
    if not isinstance(customer_id, int) or not isinstance(product, str):
        return jsonify({"error": "customer_id and product are required"}), 400
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({"error": "quantity must be a positive integer"}), 400
    price = catalog.price_of(product)
    if price is None:
        return jsonify({"error": f"unknown product: {product}"}), 400
    total = round(price * quantity, 2)

    with LegacySession() as legacy:
        credit = legacy.get(CustomerCredit, customer_id)
        if credit is None:
            return jsonify({"error": "customer not found"}), 404
        if float(credit.used) + total > float(credit.credit_limit):
            return jsonify({"error": "credit limit exceeded"}), 402
        credit.used = Decimal(str(float(credit.used) + total))
        legacy.commit()

    with Session() as db:
        order = Order(customer_id=customer_id, product=product, quantity=quantity, total=total)
        db.add(order)
        db.commit()
        result = order.to_dict()

    audit.record(result["id"], "created", {"total": total})
    events.publish("order.created", {"order_id": result["id"]})
    return jsonify(result), 201


@api.get("/orders/<int:order_id>")
def get_order(order_id: int):
    with Session() as db:
        order = db.get(Order, order_id)
        if order is None:
            return jsonify({"error": "order not found"}), 404
        return jsonify(order.to_dict())


@api.get("/orders")
def list_orders():
    customer_id = request.args.get("customer_id", type=int)
    with Session() as db:
        query = db.query(Order).order_by(Order.id)
        if customer_id is not None:
            query = query.filter(Order.customer_id == customer_id)
        return jsonify([o.to_dict() for o in query.all()])


@api.get("/orders/<int:order_id>/audit")
def order_audit(order_id: int):
    return jsonify(audit.history(order_id))
