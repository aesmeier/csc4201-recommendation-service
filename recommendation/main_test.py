import pytest
import responses
import main


@pytest.fixture
def client():
    main.app.testing = True
    return main.app.test_client()


CATALOG = [
    {"product_id": "1", "name": "Mouse", "categories": ["electronics"]},
    {"product_id": "2", "name": "Keyboard", "categories": ["electronics"]},
    {"product_id": "3", "name": "Mug", "categories": ["kitchen"]},
    {"product_id": "4", "name": "Lamp", "categories": ["electronics", "home"]},
    {"product_id": "5", "name": "Notebook", "categories": ["office"]},
    {"product_id": "6", "name": "Backpack", "categories": ["accessories"]},
]


@responses.activate
def test_recommendations_excludes_cart_items(client):
    responses.add(responses.GET, f"{main.CART_SERVICE_URL}/cart/1",
                   json=[{"product_id": 1, "name": "Mouse"}], status=200)
    responses.add(responses.GET, f"{main.CATALOG_SERVICE_URL}/products",
                   json=CATALOG, status=200)

    r = client.get("/recommendations/1", headers={"Correlation-Id": "test-123"})
    assert r.status_code == 200
    ids = [p["product_id"] for p in r.get_json()]
    assert "1" not in ids


@responses.activate
def test_recommendations_prefers_matching_category(client):
    responses.add(responses.GET, f"{main.CART_SERVICE_URL}/cart/1",
                   json=[{"product_id": 1, "name": "Mouse"}], status=200)
    responses.add(responses.GET, f"{main.CATALOG_SERVICE_URL}/products",
                   json=CATALOG, status=200)

    r = client.get("/recommendations/1")
    ids = [p["product_id"] for p in r.get_json()]
    assert ids.index("2") < ids.index("3")
    assert ids.index("4") < ids.index("5")


@responses.activate
def test_recommendations_capped_at_five(client):
    responses.add(responses.GET, f"{main.CART_SERVICE_URL}/cart/2",
                   json=[], status=200)
    responses.add(responses.GET, f"{main.CATALOG_SERVICE_URL}/products",
                   json=CATALOG, status=200)

    r = client.get("/recommendations/2")
    assert len(r.get_json()) <= 5


@responses.activate
def test_cart_service_down_returns_502(client):
    responses.add(responses.GET, f"{main.CART_SERVICE_URL}/cart/1", status=500)
    r = client.get("/recommendations/1")
    assert r.status_code == 502
    assert r.get_json()["error"] == "cart service unavailable"


@responses.activate
def test_catalog_service_down_returns_502(client):
    responses.add(responses.GET, f"{main.CART_SERVICE_URL}/cart/1", json=[], status=200)
    responses.add(responses.GET, f"{main.CATALOG_SERVICE_URL}/products", status=500)
    r = client.get("/recommendations/1")
    assert r.status_code == 502
    assert r.get_json()["error"] == "catalog service unavailable"


def test_build_recommendations_unit(client):
    recs = main.build_recommendations(
        cart_items=[{"product_id": 1, "name": "Mouse"}],
        catalog=CATALOG,
    )
    ids = [p["product_id"] for p in recs]
    assert "1" not in ids