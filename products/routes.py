from flask import Blueprint, request, jsonify
from .utils import run_pipeline

langchain = Blueprint("langchain", __name__, url_prefix="/api/v1/langchain")


@langchain.route("/query", methods=["POST"])
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
