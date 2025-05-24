from sqlalchemy.exc import IntegrityError

from flask import Blueprint, current_app, jsonify, make_response, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)
from sqlalchemy import or_
import uuid
from config import db, blacklist
from models import Business, BusinessType, User, UserType

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
business = Blueprint("business", __name__, url_prefix="/api/v1/business")


@auth.route("/signup", methods=["POST"])
def signup():
    """
    Endpoint to handle user signup.
    """
    data = request.get_json()

    required_fields = [
        "firstName",
        "lastName",
        "username",
        "password",
        "email",
        "userType",
    ]
    missing_fields = [k for k in required_fields if k not in data or data[k] is None]

    if missing_fields:
        return (
            jsonify(
                {"error": "Missing required fields", "missing_fields": missing_fields}
            ),
            400,
        )
    try:
        user_type = UserType.query.filter_by(name=data["userType"]).first()
        if not user_type:
            return make_response(
                jsonify(
                    {
                        "error": "Invalid user type",
                        "developer Message": "User Type doesn't exist",
                    }
                ),
                400,
            )
        existing_user = User.query.filter(
            or_(User.username == data["username"], User.email == data["email"])
        ).first()

        if existing_user:
            return make_response(
                jsonify(
                    {
                        "error": "User already exists",
                        "developer Message": "Username or email already taken",
                    }
                ),
                400,
            )
        new_user = User(
            id=str(uuid.uuid4())[:9],
            first_name=data["firstName"],
            middle_name=data.get("middleName"),
            last_name=data["lastName"],
            username=data["username"],
            email=data["email"],
            user_type_id=user_type.id,
        )
        new_user.set_password(data["password"])

        db.session.add(new_user)
        db.session.commit()
        return make_response(
            jsonify(
                {
                    "message": "User created successfully",
                    "developer Message": "New User Entry created",
                }
            ),
            201,
        )
    except IntegrityError as e:
        db.session.rollback()
        error_message = str(e.orig)
        return make_response(jsonify({"msg": f" {error_message}"}), 400)

    except Exception as e:
        db.session.rollback()
        error_msg = str(e).split("\n")[0]

        return make_response(jsonify({"msg": error_msg}), 400)
    finally:
        db.session.close()


@auth.route("/signin", methods=["POST"])
def signin():
    """
    Endpoint to handle user signin.
    """
    data = request.get_json()

    required_fields = ["username", "password"]
    missing_fields = [k for k in required_fields if k not in data or data[k] is None]

    if missing_fields:
        return (
            jsonify(
                {"error": "Missing required fields", "missing_fields": missing_fields}
            ),
            400,
        )
    try:
        user = User.query.filter_by(username=data["username"]).first()
        if not user or not user.check_password(data["password"]):
            return make_response(
                jsonify({"error": "Invalid username or password"}), 401
            )

        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                "email": user.email,
                "role": user.user_type,
            },
        )
        refresh_token = create_refresh_token(identity=user.id)
        return make_response(
            jsonify(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user.to_dict(),
                }
            ),
            200,
        )
    except Exception as e:
        return make_response(jsonify({"msg": str(e)}), 400)


# Assume you have a set to store blacklisted tokens
@auth.route("/check", methods=["POST"])
def check_username_email():
    """
    Endpoint to check if a username or email is already taken.
    """
    data = request.get_json()
    is_username = data.get("is_username", False)
    if is_username:
        username = data.get("username")
        if not username:
            return make_response(
                jsonify({"error": "Username is required to check availability"}), 400
            )
        user = User.query.filter_by(username=username).first()
        if user:
            return make_response(
                jsonify({"available": False, "message": "Username already taken"}), 200
            )
        return make_response(
            jsonify({"available": True, "message": "Username is available"}), 200
        )
    else:
        email = data.get("email")
        if not email:
            return make_response(jsonify({"error": "Email is required"}), 400)
        user = User.query.filter_by(email=email).first()
        if user:
            return make_response(
                jsonify({"available": False, "message": "Email already taken"}), 200
            )
        return make_response(
            jsonify({"available": True, "message": "Email is available"}), 200
        )


@auth.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Endpoint to refresh the JWT token."""
    current_user = get_jwt_identity()
    user = User.query.get(current_user)
    if not user:
        return make_response(jsonify({"error": "User not found"}), 404)

    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            "email": user.email,
            "role": user.user_type,
        },
    )
    return make_response(jsonify({"access_token": access_token}), 200)


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


@business.route("/business/getall", methods=["GET"])
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


@business.route("/business/getone/<string:business_id>", methods=["GET"])
def get_business_by_id(business_id):
    """Endpoint to get a business by its ID."""
    try:
        business = Business.query.get_or_404(business_id)
        return make_response(jsonify(business.to_dict()), 200)
    except Exception as e:
        return make_response(jsonify({"message": str(e)}), 400)


@business.route("/business/patch/<string:business_id>", methods=["PATCH"])
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


@auth.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Endpoint to handle user logout. Blacklist the JWT token."""
    jti = get_jwt()["jti"]
    blacklist.add(jti)
    return make_response(jsonify({"message": "Logged out successfully"}), 200)
