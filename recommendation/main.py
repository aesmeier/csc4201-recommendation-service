import os
import logging
import requests
from flask import Flask, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

CART_SERVICE_URL = os.environ.get("CART_SERVICE_URL", "http://localhost:8081")
CATALOG_SERVICE_URL = os.environ.get("CATALOG_SERVICE_URL", "http://localhost:8082")


def get_cart(user_id):
    resp = requests.get(f"{CART_SERVICE_URL}/cart/{user_id}", timeout=5)
    resp.raise_for_status()
    return resp.json()


def get_catalog():
    resp = requests.get(f"{CATALOG_SERVICE_URL}/products", timeout=5)
    resp.raise_for_status()
    return resp.json()


def build_recommendations(cart_items, catalog, limit=5):
    """Recommend products sharing a category with what's already in the cart,
    excluding items already in the cart. Falls back to the first N catalog
    items if nothing scores above zero (e.g. empty cart)."""
    cart_ids = {item["product_id"] for item in cart_items}

    cart_categories = set()
    for product in catalog:
        if product["product_id"] in cart_ids:
            cart_categories.update(product.get("categories", []))

    candidates = [p for p in catalog if p["product_id"] not in cart_ids]

    def score(product):
        return len(set(product.get("categories", [])) & cart_categories)

    candidates.sort(key=score, reverse=True)
    return candidates[:limit]


@app.route("/recommendations/<user_id>")
def recommendations(user_id):
    app.logger.info("GET /recommendations/%s", user_id)
    cart_items = get_cart(user_id)
    catalog = get_catalog()
    recs = build_recommendations(cart_items, catalog)
    return jsonify(recs)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))