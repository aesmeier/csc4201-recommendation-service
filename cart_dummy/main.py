import logging
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# in-memory "DB" standing in for Redis, keyed by user_id
CARTS = {
    "user1": [{"product_id": "1", "quantity": 1}, {"product_id": "3", "quantity": 2}],
    "user2": [{"product_id": "8", "quantity": 1}],
}


@app.route("/cart/<user_id>", methods=["GET", "POST", "DELETE"])
def cart(user_id):
    if request.method == "GET":
        app.logger.info("GET /cart/%s", user_id)
        return jsonify(CARTS.get(user_id, []))

    if request.method == "POST":
        item = request.get_json(force=True)
        app.logger.info("POST /cart/%s body=%s", user_id, item)
        CARTS.setdefault(user_id, []).append(item)
        return jsonify(CARTS[user_id]), 201

    # DELETE
    app.logger.info("DELETE /cart/%s", user_id)
    CARTS[user_id] = []
    return "", 204


if __name__ == "__main__":
    import os
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))