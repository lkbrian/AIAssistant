from flask import Blueprint, make_response, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import (
    Business,
    Category,
    EntityMedia,
    EntityMediaType,
    Product,
)
from .utils import run_pipeline, upload_file_to_azure
from flask_jwt_extended import jwt_required
from config import db
from .groq import (
    execute_product_query,
    get_groq_response,
    get_groq_response_multiple_queries,
    query_groq,
    sanitize_sql_query,
)

products = Blueprint("products", __name__, url_prefix="/api/v1/products")


@products.route("/create", methods=["POST"])
@jwt_required("business_owner")
def create_product():
    """
    Endpoint to create a new product.
    """
    data = request.form
    required_fields = [
        "name",
        "description",
        "category",
        "stock",
        "price",
        "businessName",
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
        business = Business.query.filter_by(name=data["businessName"]).first()
        if not business:
            return make_response(jsonify({"error": "Business not found"}), 404)
        files = request.files.getlist("media")
        print(files)

        product = Product(
            name=data["name"],
            description=data["description"],
            category_id=category.id,
            stock=int(data["stock"]),
            price=float(data["price"]),
            rating=data.get("rating", 0.0),
            business_id=business.id,
        )
        db.session.add(product)
        db.session.flush()
        entity_type = EntityMediaType.query.filter_by(name="product").first()
        if not entity_type:
            return make_response(jsonify({"error": "Entity type not found"}), 404)
        files = request.files.getlist("media")
        uploaded_urls = []
        for idx, file_obj in enumerate(files):
            # Create unique blob name, you could use UUID or product ID for structure
            safe_filename = secure_filename(file_obj.filename)
            blob_name = f"products/{product.id}/{idx}_{safe_filename}"
            result = upload_file_to_azure(file_obj, blob_name)

            if isinstance(result, dict) and result.get("url"):
                url = result["url"]
                uploaded_urls.append(url)

                # Create entity media record
                entity_media = EntityMedia(
                    entity_id=product.id,
                    entity_type_id=entity_type.id,
                    url=url,
                    storage_type=2,  # Assuming 2 means Azure
                )
                db.session.add(entity_media)

            else:
                current_app.logger.error(f"Upload failed: {result}")
                return make_response(
                    jsonify(
                        {"error": f"Failed to upload media file: {file_obj.filename}"}
                    ),
                    500,
                )

        # Optional: save the first image as product's display image
        if uploaded_urls:
            product.image_url = uploaded_urls[0]

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


@products.route("/getone/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """
    Endpoint to retrieve a product by its ID.
    """
    product = Product.query.get(product_id)
    if not product:
        return make_response(jsonify({"error": "Product not found"}), 404)

    media = EntityMedia.query.filter_by(
        entity_id=product.id,
        entity_type=EntityMediaType.query.filter_by(name="product").first().id,
    ).all()
    product.media = [m.url for m in media]

    if not product.media:
        product.media = []
    return make_response(jsonify(product.to_dict()))


@products.route("/getall", methods=["GET"])
def get_products():
    """
    Endpoint to retrieve paginated products, supports filtering by category.
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    category = request.args.get("category", type=int)

    existing_category = None
    if category:
        existing_category = Category.query.filter_by(name=category).first()
        if not existing_category:
            return make_response(jsonify({"error": "Category not found"}), 404)

    query = Product.query
    if existing_category:
        query = query.filter_by(category_id=existing_category.id)

    products_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = [product.to_dict() for product in products_pagination.items]

    return make_response(
        jsonify(
            {
                "items": products,
                "total": products_pagination.total,
                "pages": products_pagination.pages,
                "page": products_pagination.page,
                "per_page": products_pagination.per_page,
                "has_next": products_pagination.has_next,
                "has_prev": products_pagination.has_prev,
            }
        )
    )


@products.route("/patch/<int:product_id>", methods=["PATCH"])
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

    category = None
    if data.get("category"):
        category = Category.query.filter_by(name=data.get("category")).first()
        if not category:
            return make_response(jsonify({"error": "Category not found"}), 404)

    product.name = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.category_id = category.id if category else product.category_id
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


@products.route("/query-products", methods=["POST"])
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


@products.route("/nlp_search/products", methods=["POST"])
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


@products.route("/nlp_search/products/multiple", methods=["POST"])
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
