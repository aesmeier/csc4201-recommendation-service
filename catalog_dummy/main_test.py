import pytest
import main


@pytest.fixture
def client():
    main.app.testing = True
    return main.app.test_client()


def test_list_all_products(client):
    r = client.get("/products")
    assert r.status_code == 200
    assert len(r.get_json()) == len(main.PRODUCTS)


def test_search_products(client):
    r = client.get("/products?search=keyboard")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Mechanical Keyboard"


def test_get_single_product(client):
    r = client.get("/products/3")
    assert r.status_code == 200
    assert r.get_json()["name"] == "Coffee Mug"


def test_get_missing_product(client):
    r = client.get("/products/does-not-exist")
    assert r.status_code == 404