# MarketAI API Endpoints

This document contains all the API endpoints for the MarketAI backend with example curl commands, organized by resource type.

## Authentication

### Register User
```bash
curl --location 'http://localhost:5555/api/v1/auth/signup' \
--header 'Content-Type: application/json' \
--data '{
    "firstName": "John",
    "lastName": "Doe",
    "middleName": "",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
    "userType": "business_owner"
}'
```

### Login
```bash
curl --location 'http://localhost:5555/api/v1/auth/signin' \
--header 'Content-Type: application/json' \
--data '{
    "username": "johndoe",
    "password": "securepassword123"
}'
```

### Check Username/Email Availability
```bash
curl --location 'http://localhost:5555/api/v1/auth/check' \
--header 'Content-Type: application/json' \
--data '{
    "is_username": true,
    "username": "johndoe"
}'
```

```bash
curl --location 'http://localhost:5555/api/v1/auth/check' \
--header 'Content-Type: application/json' \
--data '{
    "is_username": false,
    "email": "john@example.com"
}'
```

### Refresh Token
```bash
curl --location 'http://localhost:5555/api/v1/auth/refresh' \
--header 'Authorization: Bearer YOUR_REFRESH_TOKEN'
```

### Get Current User
```bash
curl --location 'http://localhost:5555/api/v1/auth/currentuser' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN'
```

### Logout
```bash
curl --location 'http://localhost:5555/api/v1/auth/logout' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN'
```

## Business

### Create Business
```bash
curl --location 'http://localhost:5555/api/v1/business/create' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "TechStore",
    "businessType": "ecommerce",
    "location": "123 Main St, City",
    "hospitalityType": 0,
    "phoneNumber": "+1234567890",
    "email": "contact@techstore.com"
}'
```

### Get All Businesses
```bash
curl --location 'http://localhost:5555/api/v1/business/getall'
```

### Get Business by ID
```bash
curl --location 'http://localhost:5555/api/v1/business/getone/business_id'
```

### Update Business
```bash
curl --location --request PATCH 'http://localhost:5555/api/v1/business/patch/business_id' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "TechStore Plus",
    "location": "456 Oak St, City",
    "phoneNumber": "+1987654321",
    "businessType": "ecommerce"
}'
```

### Get Business Profile (Current User's Business)
```bash
curl --location 'http://localhost:5555/api/v1/business/profile' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN'
```

## Categories

### Get All Categories
```bash
curl --location 'http://localhost:5555/api/v1/categories/categories'
```

### Get Category by ID
```bash
curl --location 'http://localhost:5555/api/v1/categories/1'
```

### Create Category
```bash
curl --location 'http://localhost:5555/api/v1/categories/create' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Electronics",
    "description": "Electronic devices and accessories"
}'
```

### Update Category
```bash
curl --location --request PATCH 'http://localhost:5555/api/v1/categories/patch/1' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Consumer Electronics",
    "description": "Consumer electronic devices and accessories"
}'
```

## Products

### Create Product
```bash
curl --location 'http://localhost:5555/api/v1/products/create' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--form 'name="Wireless Headphones"' \
--form 'description="High-quality wireless headphones with noise cancellation"' \
--form 'category="Electronics"' \
--form 'stock="50"' \
--form 'price="99.99"' \
--form 'businessName="TechStore"' \
--form 'media=@"/path/to/headphones.jpg"'
```

### Get Product by ID
```bash
curl --location 'http://localhost:5555/api/v1/products/getone/1'
```

### Get All Products (with pagination)
```bash
curl --location 'http://localhost:5555/api/v1/products/getall?page=1&per_page=10'
```

### Get Products by Category
```bash
curl --location 'http://localhost:5555/api/v1/products/getall?category=Electronics&page=1&per_page=10'
```

### Update Product
```bash
curl --location --request PATCH 'http://localhost:5555/api/v1/products/patch/1' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Premium Wireless Headphones",
    "price": 129.99,
    "stock": 45,
    "category": "Electronics"
}'
```

### LangChain Query
```bash
curl --location 'http://localhost:5555/api/v1/products/langchain/query' \
--header 'Content-Type: application/json' \
--data '{
    "query": "Show me headphones"
}'
```

### Natural Language Product Search (Single Query)
```bash
curl --location 'http://localhost:5555/api/v1/products/nlp_search/products' \
--header 'Content-Type: application/json' \
--data '{
    "message": "I want a tv and headphones below kes 1000"
}'
```

### Natural Language Product Search (Multiple Queries)
```bash
curl --location 'http://localhost:5555/api/v1/products/nlp_search/products/multiple' \
--header 'Content-Type: application/json' \
--data '{
    "message": "I want a tv and headphones below kes 1000"
}'
```

### Query Products
```bash
curl --location 'http://localhost:5555/api/v1/products/query-products' \
--header 'Content-Type: application/json' \
--data '{
    "message": "Show me the best smartphones under $500"
}'
```

## Foods

### Create Food Item
```bash
curl --location 'http://localhost:5555/api/v1/foods/create' \
--form 'name="Margherita Pizza"' \
--form 'description="Classic pizza with tomato sauce and mozzarella"' \
--form 'price="12.99"' \
--form 'category="Italian"' \
--form 'businessName="PizzaPlace"' \
--form 'isAvailable="true"' \
--form 'media=@"/path/to/pizza.jpg"'
```

### Get All Food Items
```bash
curl --location 'http://localhost:5555/api/v1/foods/getall'
```

### Get Food Items by Category
```bash
curl --location 'http://localhost:5555/api/v1/foods/getall?category=Italian&page=1&per_page=10'
```

### Get Food Item by ID
```bash
curl --location 'http://localhost:5555/api/v1/foods/getone/1'
```

### Update Food Item
```bash
curl --location --request PATCH 'http://localhost:5555/api/v1/foods/patch/1' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Deluxe Margherita Pizza",
    "price": 14.99,
    "isAvailable": true,
    "category": "Premium Italian"
}'
```

## Accommodations

### Create Accommodation
```bash
curl --location 'http://localhost:5555/api/v1/accommodations/create' \
--form 'name="Deluxe Suite"' \
--form 'description="Spacious suite with ocean view"' \
--form 'price="199.99"' \
--form 'location="5th Floor, Ocean Wing"' \
--form 'status="available"' \
--form 'roomType="Suite"' \
--form 'media=@"/path/to/suite.jpg"'
```

### Get All Accommodations
```bash
curl --location 'http://localhost:5555/api/v1/accommodations/getall'
```

### Get Accommodations by Room Type
```bash
curl --location 'http://localhost:5555/api/v1/accommodations/getall?roomType=Suite&page=1&per_page=10'
```

### Get Accommodation by ID
```bash
curl --location 'http://localhost:5555/api/v1/accommodations/getone/1'
```

### Update Accommodation
```bash
curl --location --request PATCH 'http://localhost:5555/api/v1/accommodations/patch/1' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Premium Deluxe Suite",
    "price": 249.99,
    "status": "booked",
    "roomType": "Premium Suite"
}'
```

## Properties

### Create Property
```bash
curl --location 'http://localhost:5555/api/v1/property/create' \
--form 'name="Luxury Apartment"' \
--form 'description="Modern luxury apartment with city view"' \
--form 'bedrooms="2"' \
--form 'bathrooms="2"' \
--form 'land_size="1200 sq ft"' \
--form 'price="350000"' \
--form 'location="Downtown"' \
--form 'status="for_sale"' \
--form 'year_built="2020"' \
--form 'category="Residential"' \
--form 'businessType="property"' \
--form 'media=@"/path/to/apartment.jpg"'
```

### Get All Properties
```bash
curl --location 'http://localhost:5555/api/v1/property/getall'
```

### Get Properties by Category
```bash
curl --location 'http://localhost:5555/api/v1/property/getall?category=Residential&page=1&per_page=10'
```

### Get Property by ID
```bash
curl --location 'http://localhost:5555/api/v1/property/getone/1'
```

### Update Property
```bash
curl --location --request PATCH 'http://localhost:5555/api/v1/property/patch/1' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Premium Luxury Apartment",
    "price": 375000,
    "status": "for_sale"
}'
```

## Database Management

### Initialize Database with Seed Data
```shell
docker cp seed.sql $(docker compose ps -q db):/seed.sql
docker compose exec db psql -U postgres -d postgres -f /seed.sql
```

### Access Database
```shell
docker compose exec db psql -U postgres -d postgres
```

### Check Database Tables
```shell
# After accessing the database with the command above
\dt
select * from products;
```

## Entity Relationships

The MarketAI backend has the following key entity relationships:

1. **Users** - Can be business owners or regular users
   - A user can own multiple businesses

2. **Businesses** - Owned by users and categorized by business type
   - A business can have multiple products, foods, accommodations, or properties
   - Business types include: ecommerce, restaurant, property, etc.

3. **Products** - Belong to a business and are categorized
   - Products have media attachments (images)
   - Products can be searched using natural language queries

4. **Foods** - Belong to a business and are categorized
   - Foods have media attachments (images)
   - Foods can be available or unavailable

5. **Accommodations** - Belong to a business and have room types
   - Accommodations have media attachments (images)
   - Accommodations have statuses: available, unavailable, booked, maintenance

6. **Properties** - Belong to a business and have property types
   - Properties have media attachments (images)
   - Properties have statuses: for_sale, for_rent, sold, leased

7. **Categories** - Used to categorize products and foods

8. **Media** - All entities can have associated media files
   - Media is stored with entity type and entity ID references
