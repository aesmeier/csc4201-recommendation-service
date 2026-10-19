import os
import logging
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from logging_helper import log_event

app = Flask(__name__)
CORS(app, origins=[
    os.environ.get('CORS_LOCALHOST', 'http://localhost:5173'),
    os.environ.get('CORS_URL', 'https://frontend-service-887823769496.us-central1.run.app')
])
logging.basicConfig(level=logging.INFO)

CART_SERVICE_URL = os.environ.get("CART_SERVICE_URL", "https://cart-service-887823769496.us-central1.run.app")
CATALOG_SERVICE_URL = os.environ.get("CATALOG_SERVICE_URL", "https://catalog-dummy-puujfj4w6q-uc.a.run.app")


def get_cart(user_id, corr_id):
    resp = requests.get(
        f"{CART_SERVICE_URL}/cart/{user_id}",
        headers={"Correlation-Id": corr_id},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def get_catalog(corr_id):
    resp = requests.get(
        f"{CATALOG_SERVICE_URL}/products",
        headers={"Correlation-Id": corr_id},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def build_recommendations(cart_items, catalog, limit=5):
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
    corr_id = request.headers.get("Correlation-Id", "none")
    log_event(app.logger, f"GET /recommendations/{user_id}")

    try:
        cart_items = get_cart(user_id, corr_id)
    except requests.RequestException as e:
        log_event(app.logger, f"Cart service error: {e}")
        return jsonify({"error": "cart service unavailable"}), 502

    try:
        catalog = get_catalog(corr_id)
    except requests.RequestException as e:
        log_event(app.logger, f"Catalog service error: {e}")
        return jsonify({"error": "catalog service unavailable"}), 502

    recs = build_recommendations(cart_items, catalog)
    log_event(app.logger, f"returning {len(recs)} recommendations")
    return jsonify(recs)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))