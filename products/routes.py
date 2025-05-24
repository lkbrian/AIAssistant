from flask import Blueprint, make_response, request, jsonify

from models import BusinessType, Category, EntityMedia, EntityMediaType, Product
from .utils import run_pipeline
from flask_jwt_extended import jwt_required
from config import db

products = Blueprint("products", __name__, url_prefix="/api/v1/products")


@products.route("/create", methods=["POST"])
@jwt_required("business_owner")
def create_product():
    """
    Endpoint to create a new product.
    """
    data = request.form()
    required_fields = [
        "name",
        "description",
        "category",
        "stock",
        "price",
        "businessType",
    ]
    missing_fields = [k for k in required_fields if not data.get(k)]
    if "media" not in request.files:
        missing_fields.append("media")

    if missing_fields:
        return make_response(
            jsonify(
                {"error": "Missing required fields", "missing_fields": missing_fields}
            ),
            400,
        )
    try:
        category = Category.query.filter_by(name=data["category"]).first()
        if not category:
            return make_response(jsonify({"error": "Category not found"}), 404)
        business_type = BusinessType.query.filter_by(name=data["businessType"]).first()
        if not business_type:
            return make_response(jsonify({"error": "Business type not found"}), 404)

        files = request.files.getlist("media")
        print(files)

        product = Product(
            name=data["name"],
            description=data["description"],
            category_id=category.id,
            stock=int(data["stock"]),
            price=float(data["price"]),
            rating=data.get("rating", 0.0),
            business_id=business_type.id,
        )
        db.session.add(product)
        db.session.flush()
        entity_type = EntityMediaType.query.filter_by(name="product").first()
        if not entity_type:
            return make_response(jsonify({"error": "Entity type not found"}), 404)
        entity_media = EntityMedia(
            entity_id=product.id,
            entity_type_id=entity_type.id,
            url="",
            storage_type=1,  # Assuming 1 is for local storage
        )
        db.session.add(entity_media)
        db.session.commit()

        return make_response(
            jsonify(
                {
                    "message": "Product created successfully",
                    "product": product.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@products.route("/product/getone/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """
    Endpoint to retrieve a product by its ID.
    """
    product = Product.query.get(product_id)
    if not product:
        return make_response(jsonify({"error": "Product not found"}), 404)

    return make_response(jsonify({"product": product.to_dict()}))


@products.route("/products/getall", methods=["GET"])
def get_products():
    """
    Endpoint to retrieve all products.
    """
    products_list = Product.query.all()
    return make_response(
        jsonify({"products": [product.to_dict() for product in products_list]})
    )


@products.route("/product/patch/<int:product_id>", methods=["PATCH"])
@jwt_required("business_owner")
def patch_product(product_id):
    """
    Endpoint to update a product by its ID.
    """
    data = request.get_json()
    if not data:
        return make_response(jsonify({"error": "Invalid input"}), 400)

    product = Product.query.get(product_id)
    if not product:
        return make_response(jsonify({"error": "Product not found"}), 404)

    category = Category.query.filter_by(name=data.get("category")).first()
    if not category:
        return make_response(jsonify({"error": "Category not found"}), 404)

    product.name = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.category_id = category.id
    product.stock = int(data.get("stock", product.stock))
    product.price = float(data.get("price", product.price))
    product.rating = float(data.get("rating", product.rating))

    db.session.commit()
    return make_response(
        jsonify(
            {"message": "Product updated successfully", "product": product.to_dict()}
        )
    )


@products.route("/langchain/query", methods=["POST"])
# @jwt_required("")
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
