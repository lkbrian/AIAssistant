from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from models import User, Product, Category, ProductImage
from config import db

# Import directly from the groq package
from groq import (
    generate_embedding,
    query_groq,
    execute_product_query,
    sanitize_sql_query,
    get_groq_response,
    get_groq_response_multiple_queries,
    search_products_by_embedding,
)
from sqlalchemy.exc import SQLAlchemyError

# Create blueprints
groq = Blueprint("groq", __name__, url_prefix="/api/v1/groq")
auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
# langchain = Blueprint("langchain", __name__, url_prefix="/api/v1/langchain")


# Auth routes
@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validate required fields
    if not all(k in data for k in ["username", "email", "password"]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user already exists
    if (
        User.query.filter_by(username=data["username"]).first()
        or User.query.filter_by(email=data["email"]).first()
    ):
        return jsonify({"error": "Username or email already exists"}), 409

    # Create new user
    user = User(username=data["username"], email=data["email"])
    user.set_password(data["password"])

    try:
        db.session.add(user)
        db.session.commit()

        # Generate access token
        access_token = create_access_token(identity=user.id)

        return (
            jsonify(
                {
                    "message": "User registered successfully",
                    "user": user.to_dict(),
                    "access_token": access_token,
                }
            ),
            201,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    # Validate required fields
    if not all(k in data for k in ["username", "password"]):
        return jsonify({"error": "Missing username or password"}), 400

    # Find user
    user = User.query.filter_by(username=data["username"]).first()

    # Check password
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    # Generate access token
    access_token = create_access_token(identity=user.id)

    return (
        jsonify(
            {
                "message": "Login successful",
                "user": user.to_dict(),
                "access_token": access_token,
            }
        ),
        200,
    )


@auth.route("/me", methods=["GET"])
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200


# Product routes
@groq.route("/products", methods=["GET"])
def get_products():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    category = request.args.get("category", type=int)

    query = Product.query

    if category:
        query = query.filter_by(category=category)

    products = query.paginate(page=page, per_page=per_page)

    return (
        jsonify(
            {
                "products": [product.to_dict() for product in products.items],
                "total": products.total,
                "pages": products.pages,
                "page": page,
            }
        ),
        200,
    )


@groq.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product.to_dict()), 200


@groq.route("/products", methods=["POST"])
@jwt_required()
def create_product():
    data = request.get_json()

    # Validate required fields
    if not all(k in data for k in ["name", "price", "category"]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if category exists
    category = Category.query.get(data["category"])
    if not category:
        return jsonify({"error": "Category not found"}), 404

    # Create product
    product = Product(
        name=data["name"],
        description=data.get("description", ""),
        price=data["price"],
        category=data["category"],
        stock=data.get("stock", 0),
        image_url=data.get("image_url", ""),
        rating=data.get("rating", 0),
    )

    # Generate embedding for product description
    if data.get("description"):
        product.embedding = generate_embedding(data["description"])

    try:
        db.session.add(product)
        db.session.commit()

        # Add product images if provided
        if "images" in data and isinstance(data["images"], list):
            for image_url in data["images"]:
                image = ProductImage(product_id=product.id, url=image_url)
                db.session.add(image)
            db.session.commit()

        return (
            jsonify(
                {
                    "message": "Product created successfully",
                    "product": product.to_dict(),
                }
            ),
            201,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@groq.route("/products/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()

    # Update product fields
    if "name" in data:
        product.name = data["name"]
    if "description" in data:
        product.description = data["description"]
        # Update embedding if description changes
        product.embedding = generate_embedding(data["description"])
    if "price" in data:
        product.price = data["price"]
    if "category" in data:
        # Check if category exists
        category = Category.query.get(data["category"])
        if not category:
            return jsonify({"error": "Category not found"}), 404
        product.category = data["category"]
    if "stock" in data:
        product.stock = data["stock"]
    if "image_url" in data:
        product.image_url = data["image_url"]
    if "rating" in data:
        product.rating = data["rating"]

    try:
        db.session.commit()

        # Update product images if provided
        if "images" in data and isinstance(data["images"], list):
            # Remove existing images
            ProductImage.query.filter_by(product_id=product.id).delete()

            # Add new images
            for image_url in data["images"]:
                image = ProductImage(product_id=product.id, url=image_url)
                db.session.add(image)
            db.session.commit()

        return (
            jsonify(
                {
                    "message": "Product updated successfully",
                    "product": product.to_dict(),
                }
            ),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@groq.route("/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    try:
        db.session.delete(product)
        db.session.commit()

        return jsonify({"message": "Product deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Category routes
@groq.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.all()

    return jsonify({"categories": [category.to_dict() for category in categories]}), 200


@groq.route("/categories/<int:category_id>", methods=["GET"])
def get_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        return jsonify({"error": "Category not found"}), 404

    return jsonify(category.to_dict()), 200


@groq.route("/categories", methods=["POST"])
@jwt_required()
def create_category():
    data = request.get_json()

    # Validate required fields
    if "name" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    # Create category
    category = Category(name=data["name"], description=data.get("description", ""))

    try:
        db.session.add(category)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Category created successfully",
                    "category": category.to_dict(),
                }
            ),
            201,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@groq.route("/categories/<int:category_id>", methods=["PUT"])
@jwt_required()
def update_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        return jsonify({"error": "Category not found"}), 404

    data = request.get_json()

    # Update category fields
    if "name" in data:
        category.name = data["name"]
    if "description" in data:
        category.description = data["description"]

    try:
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Category updated successfully",
                    "category": category.to_dict(),
                }
            ),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@groq.route("/categories/<int:category_id>", methods=["DELETE"])
@jwt_required()
def delete_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        return jsonify({"error": "Category not found"}), 404

    # Check if category has products
    if Product.query.filter_by(category=category_id).first():
        return (
            jsonify({"error": "Cannot delete category with associated products"}),
            400,
        )

    try:
        db.session.delete(category)
        db.session.commit()

        return jsonify({"message": "Category deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# AI Assistant routes
@groq.route("/query-products", methods=["POST"])
def query_products():
    data = request.get_json()

    if "message" not in data:
        return jsonify({"error": "Missing message parameter"}), 400

    try:
        # Query GROQ for natural language processing and SQL generation
        groq_response = query_groq(data["message"])

        # Check if we have a valid SQL query
        if not groq_response or "sql_query" not in groq_response:
            return (
                jsonify(
                    {
                        "response": "Failed to generate SQL query from your request",
                        "products": [],
                    }
                ),
                400,
            )

        # Sanitize and execute the SQL query
        sql_query = sanitize_sql_query(groq_response["sql_query"])
        products = execute_product_query(sql_query)

        return (
            jsonify(
                {
                    "response": groq_response.get(
                        "response", "Query processed successfully"
                    ),
                    "products": products,
                }
            ),
            200,
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in query_products: {str(e)}")
        return (
            jsonify(
                {
                    "response": f"Error processing request: {str(e)}",
                    "products": Product.query.limit(10).all(),
                }
            ),
            500,
        )


@groq.route("/generate-embedding", methods=["POST"])
# @jwt_required()
def create_embedding():
    data = request.get_json()

    if "text" not in data:
        return jsonify({"error": "Missing text parameter"}), 400

    embedding = generate_embedding(data["text"])

    if not embedding:
        return jsonify({"error": "Failed to generate embedding"}), 500

    return jsonify({"embedding": embedding}), 200


@groq.route("/generate-embeddings/all", methods=["GET"])
# @jwt_required()
def generate_all_embeddings():
    """Generate embeddings for all products that don't have them"""
    try:
        # Get all products without embeddings
        products = Product.query.filter(Product.embedding.is_(None)).all()

        if not products:
            return (
                jsonify(
                    {"message": "No products found without embeddings", "updated": 0}
                ),
                200,
            )

        updated_count = 0

        for product in products:
            if product.description:
                # Generate embedding for product description
                embedding = generate_embedding(product.description)

                if embedding:
                    product.embedding = embedding
                    updated_count += 1

        # Commit changes to database
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Embeddings generated successfully",
                    "total_products": len(products),
                    "updated": updated_count,
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to generate embeddings: {str(e)}"}), 500


@groq.route("/nlp_search/products", methods=["POST"])
def nlp_search_products():
    """
    Enhanced natural language product search endpoint with a single comprehensive query
    that searches across all relevant fields.
    """
    data = request.get_json()

    if "message" not in data:
        return jsonify({"error": "Missing message parameter"}), 400

    try:
        # Get enhanced GROQ response with a single comprehensive query
        groq_response = get_groq_response(data["message"])

        # Check if we have a valid query
        if not groq_response or "query" not in groq_response:
            return (
                jsonify(
                    {
                        "response": "Failed to generate SQL query from your request",
                        "products": [],
                    }
                ),
                400,
            )

        # Sanitize and execute the SQL query
        sanitized_query = sanitize_sql_query(groq_response["query"])
        products = execute_product_query(sanitized_query)

        return (
            jsonify(
                {
                    "response": groq_response.get(
                        "response", "Here are some products that match your request."
                    ),
                    "products": products,
                    "query": sanitized_query,
                }
            ),
            200,
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in nlp_search_products: {str(e)}")
        return (
            jsonify(
                {
                    "response": f"Error processing request: {str(e)}",
                    "products": Product.query.limit(10).all(),
                }
            ),
            500,
        )


@groq.route("/nlp_search/products/multiple", methods=["POST"])
def nlp_search_products_multiple():
    """
    Enhanced natural language product search endpoint with multiple query interpretations
    for more comprehensive product matching.
    """
    data = request.get_json()

    if "message" not in data:
        return jsonify({"error": "Missing message parameter"}), 400

    try:
        # Get enhanced GROQ response with multiple query interpretations
        groq_response = get_groq_response_multiple_queries(data["message"])

        # Check if we have valid queries
        if (
            not groq_response
            or "queries" not in groq_response
            or not groq_response["queries"]
        ):
            return (
                jsonify(
                    {
                        "response": "Failed to generate SQL queries from your request",
                        "products": [],
                    }
                ),
                400,
            )

        # Execute all queries and collect results
        all_products = []
        query_results = []
        product_ids = set()

        for i, query in enumerate(groq_response["queries"]):
            # Sanitize the SQL query
            sanitized_query = sanitize_sql_query(query)

            # Execute the query
            products = execute_product_query(sanitized_query)

            # Add to results
            query_results.append({"query": sanitized_query, "products": products})

            # Add unique products to the combined results
            for product in products:
                if "id" in product and product["id"] not in product_ids:
                    all_products.append(product)
                    product_ids.add(product["id"])

        return (
            jsonify(
                {
                    "response": groq_response.get(
                        "response", "Here are some products that match your request."
                    ),
                    "products": all_products,
                    "interpretations": query_results,
                }
            ),
            200,
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in nlp_search_products_multiple: {str(e)}")

        # Convert Product objects to dictionaries before returning
        fallback_products = [
            product.to_dict() for product in Product.query.limit(10).all()
        ]

        return (
            jsonify(
                {
                    "response": f"Error processing request: {str(e)}",
                    "products": fallback_products,
                    "interpretations": [],
                }
            ),
            500,
        )


@groq.route("/products/semantic-search", methods=["POST"])
def semantic_search_products():
    """Search products by semantic similarity using embeddings"""
    data = request.get_json()

    if "query" not in data:
        return jsonify({"error": "Missing query parameter"}), 400

    # Get optional limit parameter, default to 10
    limit = data.get("limit", 10)

    try:
        products = search_products_by_embedding(data["query"], limit)

        return (
            jsonify(
                {
                    "response": f"Found {len(products)} products semantically similar to your query",
                    "products": products,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
