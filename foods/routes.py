from flask import Blueprint, request, make_response, jsonify
from config import db
from models import Category, Business, Food, EntityMedia, EntityMediaType
from products.utils import upload_file_to_azure
from werkzeug.utils import secure_filename

foods = Blueprint("foods", __name__, url_prefix="/api/v1/foods")


@foods.route("/create", methods=["POST"])
def create_food():
    """
    Endpoint to create a new food item.
    """
    data = request.form

    required_fields = [
        "name",
        "category",
        "businame",
        "description",
        "price",
        "isAvailable",
    ]
    missing_fields = [k for k in required_fields if k not in data or data[k] is None]
    if "media" not in request.files:
        missing_fields.append("media")

    if missing_fields:
        return {
            "error": "Missing required fields",
            "missing_fields": missing_fields,
        }, 400

    try:
        category = Category.query.filter_by(name=data["category"]).first()
        if not category:
            return make_response(jsonify({"error": "Category not found"}), 404)

        business = Business.query.filter_by(name=data["businessName"]).first()
        if not business:
            return make_response(jsonify({"error": "Business not found"}), 404)

        entity_type = EntityMediaType.query.filter_by(name="food").first()
        if not entity_type:
            return make_response(jsonify({"error": "Entity type not found"}), 404)

        food = Food(
            name=data["name"],
            description=data.get("description"),
            price=float(data["price"]),
            is_available=data.get("isAvailable", True),
            category_id=category.id,
            business_id=business.id,
        )

        db.session.add(food)
        db.session.flush()

        files = request.files.getlist("media")
        for idx, file_obj in enumerate(files):

            safe_filename = secure_filename(file_obj.filename)
            blob_name = f"foods/{food.id}/{idx}_{safe_filename}"
            result = upload_file_to_azure(file_obj, blob_name)

            if isinstance(result, dict) and result.get("url"):
                url = result.get("url")
                entity_media = EntityMedia(
                    entity_id=food.id,
                    entity_type=entity_type.id,
                    url=url,
                    storage_type=2,
                )
                db.session.add(entity_media)
        db.session.commit()

        return {"message": "Food created successfully"}, 201
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({"error": str(e)}), 500)


@foods.route("/getone/<int:food_id>", methods=["GET"])
def get_food(food_id):
    """
    Endpoint to get a single food item by ID.
    """
    food = Food.query.filter_by(id=food_id).first()
    if not food:
        return {"error": "Food not found"}, 404

    media = EntityMedia.query.filter_by(
        entity_id=food.id,
        entity_type=EntityMediaType.query.filter_by(name="food").first().id,
    ).all()
    food.media = [m.url for m in media]
    food.image_url = media[0].url if media else None
    if not food.media:
        food.media = []

    return make_response(jsonify(food.to_dict()), 200)


@foods.route("/getall", methods=["GET"])
def get_all_foods():
    """Get paginated food items"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    category = request.args.get("category", None, type=str)

    existing_category = None
    if category:
        existing_category = Category.query.filter_by(name=category).first()
        if not existing_category:
            return make_response(jsonify({"error": "Category not found"}), 404)

    query = Food.query
    if existing_category:
        query = query.filter_by(category_id=existing_category.id)

    foods_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    foods = []
    entity_type = EntityMediaType.query.filter_by(name="food").first()

    for food in foods_pagination.items:
        if not food.image_url:
            media = EntityMedia.query.filter_by(
                entity_id=food.id, entity_type_id=entity_type.id
            ).first()
            if media:
                food.image_url = media.url
        foods.append(food.to_dict())
    return make_response(
        jsonify(
            {
                "items": foods,
                "total": foods_pagination.total,
                "page": foods_pagination.page,
                "pages": foods_pagination.pages,
                "per_page": foods_pagination.per_page,
                "has_next": foods_pagination.has_next,
                "has_prev": foods_pagination.has_prev,
            }
        ),
        200,
    )


@foods.route("/patch/<int:food_id>", methods=["PATCH"])
def patch_food(food_id):
    """update a food based of an id"""
    data = request.get_json()
    food = Food.query.filter_by(id=food_id).first()
    if not food:
        return make_response(jsonify({"error": "Food not found"}), 404)
    category = None
    if data.get("category"):
        category = Category.query.filter_by(name=data.get("category")).first()
        if not category:
            return make_response(jsonify({"error": "Category not found"}), 404)

    food.name = data.get("name", food.name)
    food.description = data.get("description", food.description)
    food.price = data.get("price", food.price)
    food.is_available = data.get("isAvailable", food.is_available)
    food.category_id = category.id if category else food.category_id

    db.session.commit()
    return make_response(
        jsonify({"message": "Food updated successfully", "food": food.to_dict()}), 200
    )
