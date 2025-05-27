import uuid

from flask import Blueprint, current_app, jsonify, make_response, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)

from config import db
from models import Business, BusinessType, Category, User

category = Blueprint("categories", __name__, url_prefix="/api/v1/categories")
business = Blueprint("business", __name__, url_prefix="/api/v1/business")


@business.route("/create", methods=["POST"])
@jwt_required("business_owner")
def create_business():
    """Endpoint to create a new business profile."""
    data = request.get_json()
    current_user_id = get_jwt_identity()

    required_fields = ["name", "businessType", "location"]
    missing_fields = [k for k in required_fields if k not in data or data[k] is None]

    if missing_fields:
        return make_response(
            jsonify(
                {"error": "Missing required fields", "missing_fields": missing_fields}
            ),
            400,
        )

    try:
        busines_type = BusinessType.query.filter_by(name=data["businessType"]).first()
        if not busines_type:
            return make_response(
                jsonify(
                    {
                        "error": "Invalid business type",
                        "developer Message": "Business Type doesn't exist",
                    }
                ),
                400,
            )
        user = User.query.get_or_404(current_user_id)
        new_business = Business(
            id=str(uuid.uuid4())[:9],
            name=data["name"],
            location=data["location"],
            hospitality_type=data.get("hospitalityType"),
            email=data.get("email", user.email),
            phone_number=data.get("phoneNumber"),
            user_id=user.id,
            business_type_id=busines_type.id,
        )
        db.session.add(new_business)
        db.session.commit()
        return make_response(jsonify({"message": "Business created successfully"}), 201)
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({"msg": str(e)}), 400)
    finally:
        db.session.close()


@business.route("/getall", methods=["GET"])
def get_all_businesses():
    """Endpoint to get all businesses."""
    try:
        businesses = Business.query.all()
        return make_response(
            jsonify({"businesses": [b.to_dict() for b in businesses]}), 200
        )
        pass
    except Exception as e:
        return make_response(jsonify({"message": str(e)}), 400)


@business.route("/getone/<string:business_id>", methods=["GET"])
def get_business_by_id(business_id):
    """Endpoint to get a business by its ID."""
    try:
        business = Business.query.get_or_404(business_id)
        return make_response(jsonify(business.to_dict()), 200)
    except Exception as e:
        return make_response(jsonify({"message": str(e)}), 400)


@business.route("/patch/<string:business_id>", methods=["PATCH"])
def patch_business(business_id):
    """Endpoint to update a business profile."""
    data = request.get_json()
    try:

        business = Business.query.filter_by(id=business_id).first()
        if not business:
            return make_response(jsonify({"error": "Business not found"}), 404)
        business_type = None
        if data.get("businessType"):
            business_type = BusinessType.query.filter_by(
                name=data.get("businessType")
            ).first()
            if not business_type:
                return make_response(
                    jsonify(
                        {
                            "error": "Invalid business type",
                            "developer Message": "Business Type doesn't exist",
                        }
                    ),
                    400,
                )
        business.name = data.get("name", business.name)
        business.location = data.get("location", business.location)
        business.hospitality_type = data.get(
            "hospitalityType", business.hospitality_type
        )
        business.email = data.get("email", business.email)
        business.phone_number = data.get("phoneNumber", business.phone_number)
        business.business_type_id = (
            business_type.id if business_type else business.business_type_id
        )
        db.session.commit()

        return make_response(
            jsonify(
                {
                    "message": "Business updated successfully",
                    "business": business.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({"message": str(e)}), 400)


@business.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Endpoint to get the current user's profile."""
    current_user_id = get_jwt_identity()
    current_app.logger.info(f"Current User ID: {current_user_id}")
    if not current_user_id:
        return make_response(jsonify({"error": "User not authenticated"}), 401)
    user = User.query.get(current_user_id)
    if not user:
        return make_response(jsonify({"error": "User not found"}), 404)
    profile = Business.query.filter_by(user_id=user.id).first()
    if not profile:
        return make_response(jsonify({"error": "Business not found"}), 404)

    return make_response(jsonify(profile.to_dict()), 200)


@category.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.all()

    return jsonify({"categories": [category.to_dict() for category in categories]}), 200


@category.route("/<int:category_id>", methods=["GET"])
def get_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        return jsonify({"error": "Category not found"}), 404

    return jsonify(category.to_dict()), 200


@category.route("/create", methods=["POST"])
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
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@category.route("/patch/<int:category_id>", methods=["PATCH"])
@jwt_required()
def patch_category(category_id):
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
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# AI Assistant routes
