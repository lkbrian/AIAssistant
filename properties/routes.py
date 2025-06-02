from flask import Blueprint, make_response, request, jsonify, current_app

from models import (
    Business,
    Category,
    EntityMedia,
    EntityMediaType,
    Product,
    Property,
    PropertyType,
)

# from flask_jwt_extended import jwt_required
from config import db

property = Blueprint("property", __name__, url_prefix="/api/v1/property")


@property.route("/create", methods=["POST"])
# @jwt_required("business_owner")
def create_property():
    """
    Endpoint to create a new property.
    """
    data = request.form
    required_fields = [
        "name",
        "description",
        "bedrooms",
        "bathrooms",
        "landSize",
        "businessName",
        "propertyType",
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
        property_type = PropertyType.query.filter_by(name=data["propertyType"]).first()
        if not property_type:
            return make_response(jsonify({"error": "Property type not found"}))

        business = Business.query.filter_by(name=data["businessName"]).first()
        if not business:
            current_app.logger.warning({"warning": "Business not found"})
            return make_response(jsonify({"error": "Business not found"}), 404)

        # files = request.files.getlist("media")

        prop = Property(
            name=data["name"],
            business_id=business.id,
            property_type_id=property_type.id,
            description=data["description"],
            bedrooms=data["bedrooms"],
            land_size=data["landSize"],
            price=data["price"],
            location=data["location"],
            status=data["status"],
            year_built=data["year_built"],
        )
        db.session.add(prop)
        db.session.flush()
        entity_type = EntityMediaType.query.filter_by(name="property").first()
        if not entity_type:
            return make_response(jsonify({"error": "Entity type not found"}), 404)
        entity_media = EntityMedia(
            entity_id=prop.id,
            entity_type_id=entity_type.id,
            url="",
            storage_type=1,  # Assuming 1 is for local storage
        )
        db.session.add(entity_media)
        db.session.commit()

        return make_response(
            jsonify(
                {
                    "message": "property created successfully",
                    "product": prop.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(e)
        return make_response(jsonify({"error": str(e)}), 500)


@property.route("/getone/<int:property_id>", methods=["GET"])
def get_property(property_id):
    """
    Endpoint to retrieve a property by its ID.
    """
    property = Product.query.get(property_id)
    if not property:
        return make_response(jsonify({"error": "Property not found"}), 404)

    media = EntityMedia.query.filter_by(
        entity_id=property.id,
        entity_type=EntityMediaType.query.filter_by(name="property").first().id,
    ).all()
    property.media = [m.url for m in media]

    if not property.media:
        property.media = []
    return make_response(jsonify(property.to_dict()))


@property.route("/getall", methods=["GET"])
def get_properties():
    """
    Endpoint to retrieve paginated properties, supports filtering by category.
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    category = request.args.get("category", type=int)

    existing_category = None
    if category:
        existing_category = Category.query.filter_by(name=category).first()
        if not existing_category:
            return make_response(jsonify({"error": "Category not found"}), 404)

    query = Property.query
    if existing_category:
        query = query.filter_by(category_id=existing_category.id)

    property_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    properties = [property.to_dict() for product in property_pagination.items]

    return make_response(
        jsonify(
            {
                "items": properties,
                "total": property_pagination.total,
                "pages": property_pagination.pages,
                "page": property_pagination.page,
                "per_page": property_pagination.per_page,
                "has_next": property_pagination.has_next,
                "has_prev": property_pagination.has_prev,
            }
        )
    )


@property.route("/patch/<int:property_id>", methods=["PATCH"])
# @jwt_required("business_owner")
def update_product(property_id):
    """
    Endpoint to update a property by its ID.
    """
    data = request.get_json()
    if not data:
        return make_response(jsonify({"error": "Invalid input"}), 400)

    prop = Property.query.get(property_id)
    if not prop:
        return make_response(jsonify({"error": "Product not found"}), 404)

    prop.name = data.get("name", prop.name)
    prop.description = data.get("description", prop.description)
    prop.bedrooms = data.get("bedrooms", prop.bedrooms)
    prop.bathrooms = data.get("bathrooms", prop.bathrooms)
    prop.land_size = int(data.get("land_size", prop.land_size))
    prop.price = float(data.get("price", prop.price))
    prop.location = float(data.get("location", prop.location))
    prop.status = float(data.get("status", prop.status))
    prop.year_built = float(data.get("year_built", prop.year_built))

    db.session.commit()
    return make_response(
        jsonify(
            {"message": "Property updated successfully", "property": prop.to_dict()}
        )
    )
