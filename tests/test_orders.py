import json
import random

from app.worker import handle


def _customer(client, limit=500):
    customer_id = random.randint(1_000, 1_000_000)
    response = client.post(f"/customers/{customer_id}/credit", json={"credit_limit": limit})
    assert response.status_code == 200
    return customer_id


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_create_and_read_an_order(client):
    customer = _customer(client)
    created = client.post("/orders", json={"customer_id": customer, "product": "mouse", "quantity": 2})
    assert created.status_code == 201
    order = created.get_json()
    assert order["total"] == 39.0
    assert order["status"] == "pending"
    read = client.get(f"/orders/{order['id']}").get_json()
    # A running worker may already have confirmed it.
    assert read["status"] in ("pending", "confirmed")
    assert {**read, "status": "pending"} == order


def test_credit_is_charged_in_the_legacy_database(client):
    customer = _customer(client, limit=100)
    client.post("/orders", json={"customer_id": customer, "product": "keyboard"})
    assert client.get(f"/customers/{customer}/credit").get_json()["used"] == 49.0


def test_an_order_over_the_credit_limit_is_refused(client):
    customer = _customer(client, limit=50)
    response = client.post("/orders", json={"customer_id": customer, "product": "monitor"})
    assert response.status_code == 402


def test_unknown_product_and_unknown_customer(client):
    customer = _customer(client)
    assert client.post("/orders", json={"customer_id": customer, "product": "sofa"}).status_code == 400
    assert client.post("/orders", json={"customer_id": 1, "product": "mouse"}).status_code == 404


def test_the_worker_confirms_an_order_and_audits_it(client):
    customer = _customer(client)
    order = client.post("/orders", json={"customer_id": customer, "product": "cable"}).get_json()
    handle(json.dumps({"event": "order.created", "order_id": order["id"]}).encode())
    assert client.get(f"/orders/{order['id']}").get_json()["status"] == "confirmed"
    events = [e["event"] for e in client.get(f"/orders/{order['id']}/audit").get_json()]
    assert events == ["created", "confirmed"]


def test_orders_are_listed_per_customer(client):
    customer = _customer(client)
    client.post("/orders", json={"customer_id": customer, "product": "mouse"})
    client.post("/orders", json={"customer_id": customer, "product": "cable"})
    orders = client.get(f"/orders?customer_id={customer}").get_json()
    assert [o["product"] for o in orders] == ["mouse", "cable"]
