from flask import Blueprint, make_response, request, jsonify

from models import BusinessType, Category, EntityMedia, EntityMediaType, Product, Property
from flask_jwt_extended import jwt_required
from config import db

property = Blueprint("property", __name__, url_prefix="/api/v1/property")

@property.route("/create", methods=["POST"])
@jwt_required("business_owner")
def create_property():
    """
    Endpoint to create a new property.
    """
    data = request.form()
    required_fields = [
        "name",
        "description",
        "bedrooms",
        "bathrooms",
        "land_size",
        "price",
        "location",
        "status",
        "year_built",
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

        property = Property(
            1,'2345'
        )
        db.session.add(property)
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


