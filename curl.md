# API Endpoints

This document contains all the API endpoints for the MarketAI backend with example curl commands.

## Authentication

### Register User
```bash
curl --location 'http://localhost:5000/api/v1/auth/register' \
--header 'Content-Type: application/json' \
--data '{
    "first_name": "John",
    "last_name": "Doe",
    "middle_name": "",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
    "user_type_id": 1
}'
```

### Login
```bash
curl --location 'http://localhost:5000/api/v1/auth/login' \
--header 'Content-Type: application/json' \
--data '{
    "email": "john@example.com",
    "password": "securepassword123"
}'
```

### Logout
```bash
curl --location 'http://localhost:5000/api/v1/auth/logout' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN'
```

## Products

### Create Product
```bash
curl --location 'http://localhost:5000/api/v1/products/create' \
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
curl --location 'http://localhost:5000/api/v1/products/getone/1'
```

### Get All Products (with pagination)
```bash
curl --location 'http://localhost:5000/api/v1/products/getall?page=1&per_page=10'
```

### Get Products by Category
```bash
curl --location 'http://localhost:5000/api/v1/products/getall?category=Electronics&page=1&per_page=10'
```

### Update Product
```bash
curl --location --request PATCH 'http://localhost:5000/api/v1/products/patch/1' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Premium Wireless Headphones",
    "price": 129.99,
    "stock": 45
}'
```

### LangChain Query
```bash
curl --location 'http://localhost:5000/api/v1/products/langchain/query' \
--header 'Content-Type: application/json' \
--data '{
    "query": "Show me headphones"
}'
```

### Natural Language Product Search (Single Query)
```bash
curl --location 'http://localhost:5000/api/v1/products/nlp_search/products' \
--header 'Content-Type: application/json' \
--data '{
    "message": "I want a tv and headphones below kes 1000"
}'
```

### Natural Language Product Search (Multiple Queries)
```bash
curl --location 'http://localhost:5000/api/v1/products/nlp_search/products/multiple' \
--header 'Content-Type: application/json' \
--data '{
    "message": "I want a tv and headphones below kes 1000"
}'
```

### Query Products
```bash
curl --location 'http://localhost:5000/api/v1/products/query-products' \
--header 'Content-Type: application/json' \
--data '{
    "message": "Show me the best smartphones under $500"
}'
```

## Categories

### Create Category
```bash
curl --location 'http://localhost:5000/api/v1/category/create' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Electronics",
    "description": "Electronic devices and accessories"
}'
```

### Get All Categories
```bash
curl --location 'http://localhost:5000/api/v1/category/getall'
```

### Get Category by ID
```bash
curl --location 'http://localhost:5000/api/v1/category/getone/1'
```

### Update Category
```bash
curl --location --request PATCH 'http://localhost:5000/api/v1/category/patch/1' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Consumer Electronics",
    "description": "Consumer electronic devices and accessories"
}'
```

## Business

### Create Business
```bash
curl --location 'http://localhost:5000/api/v1/business/create' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "TechStore",
    "business_type_id": 1,
    "location": "123 Main St, City",
    "hospitality_type": 0,
    "phone_number": "+1234567890",
    "email": "contact@techstore.com"
}'
```

### Get All Businesses
```bash
curl --location 'http://localhost:5000/api/v1/business/getall'
```

### Get Business by ID
```bash
curl --location 'http://localhost:5000/api/v1/business/getone/business_id'
```

### Update Business
```bash
curl --location --request PATCH 'http://localhost:5000/api/v1/business/patch/business_id' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "TechStore Plus",
    "location": "456 Oak St, City",
    "phone_number": "+1987654321"
}'
```

## Foods

### Create Food Item
```bash
curl --location 'http://localhost:5000/api/v1/foods/create' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
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
curl --location 'http://localhost:5000/api/v1/foods/getall'
```

### Get Food Items by Category
```bash
curl --location 'http://localhost:5000/api/v1/foods/getall?category=Italian&page=1&per_page=10'
```

### Get Food Item by ID
```bash
curl --location 'http://localhost:5000/api/v1/foods/getone/1'
```

### Update Food Item
```bash
curl --location --request PATCH 'http://localhost:5000/api/v1/foods/patch/1' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
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
curl --location 'http://localhost:5000/api/v1/accommodations/create' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
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
curl --location 'http://localhost:5000/api/v1/accommodations/getall'
```

### Get Accommodations by Room Type
```bash
curl --location 'http://localhost:5000/api/v1/accommodations/getall?roomType=Suite&page=1&per_page=10'
```

### Get Accommodation by ID
```bash
curl --location 'http://localhost:5000/api/v1/accommodations/getone/1'
```

### Update Accommodation
```bash
curl --location --request PATCH 'http://localhost:5000/api/v1/accommodations/patch/1' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Premium Deluxe Suite",
    "price": 249.99,
    "status": "booked",
    "roomType": "Premium Suite"
}'
```
## Database Management

### Initialize Database with Seed Data
```shell
docker cp seed.sql $(docker compose ps -q db):/seed.sql
docker compose exec db psql -U postgres -d marketai -f /seed.sql
```

### Access Database
```shell
docker compose exec db psql -U postgres -d marketai
```

### Check Database Tables
```shell
# After accessing the database with the command above
\dt
select * from products;
```