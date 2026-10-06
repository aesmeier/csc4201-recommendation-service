import pytest
import main


@pytest.fixture
def client():
    main.app.testing = True
    main.CARTS = {"user1": [{"product_id": "1", "quantity": 1}]}  # reset state
    return main.app.test_client()


def test_get_existing_cart(client):
    r = client.get("/cart/user1")
    assert r.status_code == 200
    assert r.get_json() == [{"product_id": "1", "quantity": 1}]


def test_get_unknown_user_returns_empty(client):
    r = client.get("/cart/nobody")
    assert r.status_code == 200
    assert r.get_json() == []


def test_post_adds_item(client):
    r = client.post("/cart/user1", json={"product_id": "5", "quantity": 1})
    assert r.status_code == 201
    assert len(r.get_json()) == 2


def test_delete_empties_cart(client):
    r = client.delete("/cart/user1")
    assert r.status_code == 204
    assert main.CARTS["user1"] == []