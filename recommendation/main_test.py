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
    responses.add(responses.GET, f"{main.CART_SERVICE_URL}/cart/user1",
                   json=[{"product_id": "1", "quantity": 1}], status=200)
    responses.add(responses.GET, f"{main.CATALOG_SERVICE_URL}/products",
                   json=CATALOG, status=200)

    r = client.get("/recommendations/user1")
    assert r.status_code == 200
    ids = [p["product_id"] for p in r.get_json()]
    assert "1" not in ids  # already in cart


@responses.activate
def test_recommendations_prefers_matching_category(client):
    responses.add(responses.GET, f"{main.CART_SERVICE_URL}/cart/user1",
                   json=[{"product_id": "1", "quantity": 1}], status=200)
    responses.add(responses.GET, f"{main.CATALOG_SERVICE_URL}/products",
                   json=CATALOG, status=200)

    r = client.get("/recommendations/user1")
    ids = [p["product_id"] for p in r.get_json()]
    # product 2 and 4 share the "electronics" category with product 1
    assert ids.index("2") < ids.index("3")  # electronics ranked above kitchen
    assert ids.index("4") < ids.index("5")  # electronics ranked above office


@responses.activate
def test_recommendations_capped_at_five(client):
    responses.add(responses.GET, f"{main.CART_SERVICE_URL}/cart/user2",
                   json=[], status=200)
    responses.add(responses.GET, f"{main.CATALOG_SERVICE_URL}/products",
                   json=CATALOG, status=200)

    r = client.get("/recommendations/user2")
    assert len(r.get_json()) <= 5


def test_build_recommendations_unit(client):
    # test the pure function directly, no Flask/HTTP involved at all
    recs = main.build_recommendations(
        cart_items=[{"product_id": "1", "quantity": 1}],
        catalog=CATALOG,
    )
    ids = [p["product_id"] for p in recs]
    assert "1" not in ids