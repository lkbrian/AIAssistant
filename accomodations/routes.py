from flask import Blueprint, make_response, jsonify, request
from config import db
from models import Accommodation, EntityMedia, EntityMediaType, RoomType
from werkzeug.utils import secure_filename
from products.utils import upload_file_to_azure


accommodations = Blueprint(
    "accommodations", __name__, url_prefix="/api/v1/accommodations"
)


@accommodations.route("/create", methods=["POST"])
def create_accommodation():
    """create an accommodations"""
    data = request.form
    required_fields = ["name", "location", "description", "price", "roomType"]
    missing_fields = [k for k in required_fields if k not in data or data[k] is None]
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

        if data.get("status") not in [
            "available",
            "unavailable",
            "booked",
            "maintenance",
        ]:
            return make_response(jsonify({"error": "Invalid status value"}), 400)
        room_type = RoomType.query.filter_by(name=data.get("roomType")).first()
        if not room_type:
            return make_response(jsonify({"error": "Invalid room type"}), 400)
        entity_type = EntityMediaType.query.filter_by(name="accommodation").first()
        if not entity_type:
            return make_response(jsonify({"error": "Entity type not found"}), 404)

        accommodation = Accommodation(
            name=data["name"],
            location=data["location"],
            description=data.get("description"),
            price=data["price"],
            status=data.get("status", "available"),
            room_type_id=room_type.id,
        )
        db.session.add(accommodation)
        db.session.flush()

        files = request.files.getlist("media")
        for idx, file_obj in enumerate(files):
            safe_filename = secure_filename(file_obj.filename)
            blob_name = f"accommodations/{accommodation.id}/{idx}_{safe_filename}"
            result = upload_file_to_azure(file_obj, blob_name)
            if isinstance(result, dict) and result.get("url"):
                url = result.get("url")
                entity_media = EntityMedia(
                    entity_id=accommodation.id,
                    entity_type_id=entity_type.id,
                    url=url,
                    storage_type=2,
                )
                db.session.add(entity_media)
        db.session.commit()
        return make_response(
            jsonify(
                {
                    "message": "Accommodation created successfully",
                    "accomodation": accommodation.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return make_response(
            jsonify({"message": "An error occurred", "error": str(e)}), 500
        )


@accommodations.route("/getone/<int:accommodation_id>", methods=["GET"])
def get_accommodation(accommodation_id):
    """get a single accommodation"""
    accommodation = Accommodation.query.filter_by(id=accommodation_id).first()
    if not accommodation:
        return make_response(jsonify({"error": "Accommodation not found"}), 404)
    media = EntityMedia.query.filter_by(
        entity_id=accommodation.id,
        entity_type_id=EntityMediaType.query.filter_by(name="accommodation").first().id,
    )
    accommodation.media = [m.url for m in media]
    accommodation.image_url = media[0].url if media else None
    if not accommodation.media:
        accommodation.media = []
    return make_response(jsonify(accommodation.to_dict()), 200)


@accommodations.route("/getall", methods=["GET"])
def get_accommodations():
    """get all accommodations"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    room_type = request.args.get("roomType", None, type=str)

    existing_room_type = None
    if room_type:
        existing_room_type = RoomType.query.filter_by(name=room_type).first()
        if not existing_room_type:
            return make_response(jsonify({"error": "Invalid room type"}), 400)

    query = Accommodation.query
    if existing_room_type:
        query = query.filter_by(room_type_id=existing_room_type.id)

    accommodations_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    accommodations = []
    entity_type = EntityMediaType.query.filter_by(name="accommodation").first()
    for accommodation in accommodations_pagination.items:
        if not accommodation.image_url:
            media = EntityMedia.query.filter_by(
                entity_id=accommodation.id, entity_type_id=entity_type.id
            ).all()
            accommodation.media = [m.url for m in media]
            accommodation.image_url = media[0].url if media else None
        accommodations.append(accommodation.to_dict())

    return make_response(
        jsonify(
            {
                "items": accommodations,
                "total": accommodations_pagination.total,
                "page": accommodations_pagination.page,
                "pages": accommodations_pagination.pages,
                "per_page": accommodations_pagination.per_page,
                "has_next": accommodations_pagination.has_next,
                "has_prev": accommodations_pagination.has_prev,
            }
        ),
        200,
    )


@accommodations.route("/patch/<int:accommodation_id>", methods=["PATCH"])
def patch_accommodation(accommodation_id):
    """update an accomodation"""
    data = request.get_json()
    accommodation = Accommodation.query.filter_by(id=accommodation_id).first()
    if not accommodation:
        return make_response(jsonify({"error": "Accommodation not found"}), 404)
    if data.get("status") not in ["available", "unavailable", "booked", "maintenance"]:
        return make_response(jsonify({"error": "Invalid status value"}), 400)
    room_type = None
    if data.get("roomType"):
        room_type = RoomType.query.filter_by(name=data.get("roomType")).first()
        if not room_type:
            return make_response(jsonify({"error": "Invalid room type"}), 400)
    accommodation.name = data.get("name", accommodation.name)
    accommodation.location = data.get("location", accommodation.location)
    accommodation.description = data.get("description", accommodation.description)
    accommodation.price = data.get("price", accommodation.price)
    accommodation.status = data.get("status", accommodation.status)
    accommodation.room_type_id = (
        room_type.id if room_type else accommodation.room_type_id
    )
    db.session.commit()
    return make_response(
        jsonify(
            {
                "message": "Accommodation updated successfully",
                "accommodation": accommodation.to_dict(),
            }
        ),
        200,
    )
