from flask import Blueprint, request, jsonify
from .utils import run_pipeline
from flask_jwt_extended import jwt_required

langchain = Blueprint("langchain", __name__, url_prefix="/api/v1/langchain")
products = Blueprint("products", __name__, url_prefix="/api/v1/products")


@langchain.route("/query", methods=["POST"])
@jwt_required("admin")
def query():
    """
    Endpoint to handle SQL queries.
    """
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        result = run_pipeline(data["query"])
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
