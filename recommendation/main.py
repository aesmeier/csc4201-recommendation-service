import os
import logging
import requests
from flask import Flask, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app, origins=[
    os.environ.get('CORS_LOCALHOST', 'http://localhost:5173'),
    os.environ.get('CORS_URL', 'https://frontend-service-887823769496.us-central1.run.app')
])
logging.basicConfig(level=logging.INFO)

CART_SERVICE_URL = os.environ.get("CART_SERVICE_URL", "https://cart-service-887823769496.us-central1.run.app")
CATALOG_SERVICE_URL = os.environ.get("CATALOG_SERVICE_URL", "https://catalog-dummy-puujfj4w6q-uc.a.run.app")


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
    items if nothing scores above zero (e.g. empty cart).

    product_id is normalized to str on both sides, since Cart returns it as
    an int while Catalog returns it as a string.
    """
    cart_ids = {str(item["product_id"]) for item in cart_items}

    cart_categories = set()
    for product in catalog:
        if str(product["product_id"]) in cart_ids:
            cart_categories.update(product.get("categories", []))

    candidates = [p for p in catalog if str(p["product_id"]) not in cart_ids]

    def score(product):
        return len(set(product.get("categories", [])) & cart_categories)

    candidates.sort(key=score, reverse=True)
    return candidates[:limit]


@app.route("/recommendations/<user_id>")
def recommendations(user_id):
    app.logger.info("GET /recommendations/%s", user_id)

    try:
        cart_items = get_cart(user_id)
    except requests.RequestException as e:
        app.logger.error("Cart service error: %s", e)
        return jsonify({"error": "cart service unavailable"}), 502

    try:
        catalog = get_catalog()
    except requests.RequestException as e:
        app.logger.error("Catalog service error: %s", e)
        return jsonify({"error": "catalog service unavailable"}), 502

    recs = build_recommendations(cart_items, catalog)
    return jsonify(recs)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))