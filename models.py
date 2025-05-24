from sqlalchemy.sql import func
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import check_password_hash, generate_password_hash
from config import db
import enum


class PropertyStatus(enum.Enum):
    FOR_SALE = "for_sale"
    FOR_RENT = "for_rent"
    SOLD = "sold"
    LEASED = "leased"


class AccommodationStatus(enum.Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"


class UserType(db.Model, SerializerMixin):
    __tablename__ = "user_types"
    serialize_only = ("id", "name", "description")
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)  # admin, user
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    users = db.relationship("User", back_populates="type", lazy=True)


class User(db.Model, SerializerMixin):
    __tablename__ = "app_users"
    serialize_only = (
        "id",
        "first_name",
        "middle_name",
        "last_name",
        "username",
        "user_type_id",
        "user_type",
        "email",
        "created_at",
        "updated_at",
    )

    id = db.Column(db.String(255), primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    middle_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    user_type_id = db.Column(db.Integer, db.ForeignKey("user_types.id"), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    businesses = db.relationship("Business", back_populates="owner", lazy=True)
    type = db.relationship("UserType", back_populates="users", lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def user_type(self):
        return self.type.name if self.type else None


class BusinessType(db.Model, SerializerMixin):
    __tablename__ = "business_types"
    serialize_only = ("id", "name", "description")
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))  # ecommerce, restaurant, property
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    businesses = db.relationship("Business", back_populates="type", lazy=True)


class Business(db.Model, SerializerMixin):
    __tablename__ = "m_business"
    serialize_only = (
        "id",
        "name",
        "business_type_id",
        "business_type",
        "location",
        "hospitality_type",
        "phone_number",
        "email",
        "user_id",
        "owner_name",
        "created_at",
        "updated_at",
    )
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    business_type_id = db.Column(db.Integer, db.ForeignKey("business_types.id"))
    location = db.Column(db.String(255))
    hospitality_type = db.Column(db.Integer)
    phone_number = db.Column(db.String(255))
    email = db.Column(db.String(255))
    user_id = db.Column(db.String(255), db.ForeignKey("app_users.id"))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    products = db.relationship("Product", back_populates="business", lazy=True)
    properties = db.relationship("Property", back_populates="business", lazy=True)
    accommodations = db.relationship(
        "Accommodation", back_populates="business", lazy=True
    )
    foods = db.relationship("Food", back_populates="business", lazy=True)
    type = db.relationship("BusinessType", back_populates="businesses", lazy=True)
    owner = db.relationship("User", back_populates="businesses", lazy=True)

    @property
    def business_type(self):
        return self.type.name if self.type else None

    @property
    def owner_name(self):
        return (
            f"{self.owner.first_name} {self.owner.middle_name} {self.owner.last_name}"
            if self.owner
            else None
        )


class PropertyType(db.Model, SerializerMixin):
    __tablename__ = "property_types"
    serialize_only = ("id", "name", "description")

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))  # land, apartment, house
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    # Relationships
    properties = db.relationship("Property", back_populates="type", lazy=True)


class Property(db.Model, SerializerMixin):
    __tablename__ = "property"
    serialize_only = (
        "id",
        "business_id",
        "business_name",
        "property_type_id",
        "property_type",
        "name",
        "description",
        "bedrooms",
        "bathrooms",
        "land_size",
        "price",
        "location",
        "status",
        "year_built",
        "created_at",
        "updated_at",
    )
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.String(255), db.ForeignKey("m_business.id"), nullable=False
    )
    property_type_id = db.Column(
        db.Integer, db.ForeignKey("property_types.id"), nullable=False
    )
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    land_size = db.Column(db.String(255))
    price = db.Column(db.Numeric)
    location = db.Column(db.String(255))
    status = db.Column(db.String(255))  # For sale, for rent, sold, leased
    year_built = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    type = db.relationship("PropertyType", back_populates="properties", lazy=True)
    business = db.relationship("Business", back_populates="properties", lazy=True)

    @property
    def property_type(self):
        return self.type.name if self.type else None

    @property
    def business_name(self):
        return self.business.name if self.business else None


class RoomType(db.Model, SerializerMixin):
    __tablename__ = "room_types"
    serialize_only = ("id", "name", "description")

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255))

    # Relationships
    accommodations = db.relationship(
        "Accommodation", back_populates="room_type_rel", lazy=True
    )


class Accommodation(db.Model, SerializerMixin):
    __tablename__ = "accomodation"
    serialize_only = (
        "id",
        "business_id",
        "business_name",
        "room_type_id",
        "room_type",
        "name",
        "description",
        "bedrooms",
        "price",
        "location",
        "check_in_time",
        "check_out_time",
        "created_at",
        "updated_at",
    )
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.String(255), db.ForeignKey("m_business.id"), nullable=False
    )
    room_type_id = db.Column(
        db.Integer, db.ForeignKey("room_types.id"), nullable=False
    )  # single, double, suite
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))
    bedrooms = db.Column(db.Integer)
    price = db.Column(db.Numeric)
    location = db.Column(db.String(255))
    status = db.Column(db.String(255))
    check_in_time = db.Column(db.String(255))
    check_out_time = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    business = db.relationship("Business", back_populates="accommodations", lazy=True)
    room_type_rel = db.relationship(
        "RoomType", back_populates="accommodations", lazy=True
    )

    @property
    def business_name(self):
        return self.business.name if self.business else None

    @property
    def room_type(self):
        return self.room_type_rel.name if self.room_type_rel else None


class Category(db.Model, SerializerMixin):
    __tablename__ = "categories"
    serialize_only = ("id", "name", "description", "created_at", "updated_at")

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    products = db.relationship("Product", back_populates="category_rel", lazy=True)
    foods = db.relationship("Food", back_populates="category_rel", lazy=True)


class Food(db.Model):
    __tablename__ = "food"
    serialize_only = (
        "id",
        "business_name",
        "business_id",
        "category_id",
        "category",
        "name",
        "description",
        "price",
        "is_available",
        "created_at",
        "updated_at",
    )

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.String(255), db.ForeignKey("m_business.id"), nullable=False
    )
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))
    price = db.Column(db.Numeric)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    category_rel = db.relationship("Category", back_populates="foods", lazy=True)
    business = db.relationship("Business", back_populates="foods", lazy=True)

    # Computed property to expose category name
    @property
    def category(self):
        return self.category_rel.name if self.category_rel else None

    @property
    def business_name(self):
        return self.business.name if self.business else None


class Product(db.Model, SerializerMixin):
    __tablename__ = "products"
    serialize_only = (
        "id",
        "business_name",
        "business_id",
        "name",
        "description",
        "price",
        "category_id",
        "category",
        "stock",
        "image_url",
        "rating",
        "created_at",
        "updated_at",
    )
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.String(255), db.ForeignKey("m_business.id"), nullable=False
    )
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    stock = db.Column(db.Integer)
    image_url = db.Column(db.String(255))
    rating = db.Column(db.Integer)
    embedding = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    category_rel = db.relationship("Category", back_populates="products", lazy=True)
    business = db.relationship("Business", back_populates="products", lazy=True)

    @property
    def category(self):
        return self.category_rel.name if self.category_rel else None

    @property
    def business_name(self):
        return self.business.name if self.business else None


class EntityMedia(db.Model, SerializerMixin):
    __tablename__ = "entity_media"
    serialize_only = ("id", "entity_type", "entity_id", "url", "storage_type")
    id = db.Column(db.Integer, primary_key=True)
    entity_type_id = db.Column(
        db.Integer, db.ForeignKey("entity_media_types.id"), nullable=False
    )  # property, foods, etc.
    entity_id = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(255))
    storage_type = db.Column(db.Integer)  # bucket, in-memory
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    media_type = db.relationship(
        "EntityMediaType", back_populates="entity_media", lazy=True
    )

    @property
    def entity_type(self):
        return self.media_type.name if self.media_type else None


class EntityMediaType(db.Model, SerializerMixin):
    __tablename__ = "entity_media_types"
    serialize_only = ("id", "name", "description")
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(
        db.String(255), unique=True, nullable=False
    )  # property, food, etc.
    description = db.Column(db.String(255))

    # Relationships
    entity_media = db.relationship(
        "EntityMedia", back_populates="media_type", lazy=True
    )
