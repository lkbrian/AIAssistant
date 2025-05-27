# MarketAI API Curl Commands

This document contains all the curl commands for interacting with the MarketAI API.

## Authentication Endpoints

### User Signup
```shell
curl --location 'http://localhost:5000/api/v1/auth/signup' \
--header 'Content-Type: application/json' \
--data '{
    "firstName": "John",
    "lastName": "Doe",
    "username": "johndoe",
    "password": "securepassword",
    "email": "john.doe@example.com",
    "userType": "business_owner"
}'
```

### User Signin
```shell
curl --location 'http://localhost:5000/api/v1/auth/signin' \
--header 'Content-Type: application/json' \
--data '{
    "username": "johndoe",
    "password": "securepassword"
}'
```

### Check Username/Email Availability
```shell
curl --location 'http://localhost:5000/api/v1/auth/check' \
--header 'Content-Type: application/json' \
--data '{
    "is_username": true,
    "username": "johndoe"
}'
```

```shell
curl --location 'http://localhost:5000/api/v1/auth/check' \
--header 'Content-Type: application/json' \
--data '{
    "is_username": false,
    "email": "john.doe@example.com"
}'
```

### Refresh Token
```shell
curl --location 'http://localhost:5000/api/v1/auth/refresh' \
--header 'Authorization: Bearer YOUR_REFRESH_TOKEN'
```

### Get Current User
```shell
curl --location 'http://localhost:5000/api/v1/auth/currentuser' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### Logout
```shell
curl --location 'http://localhost:5000/api/v1/auth/logout' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

## Business Endpoints

### Create Business
```shell
curl --location 'http://localhost:5000/api/v1/business/create' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--data '{
    "name": "Business Name",
    "businessType": "ecommerce",
    "location": "Business Location",
    "hospitalityType": "Optional Hospitality Type",
    "email": "business@example.com",
    "phoneNumber": "+1234567890"
}'
```

### Get All Businesses
```shell
curl --location 'http://localhost:5000/api/v1/business/getall'
```

### Get Business by ID
```shell
curl --location 'http://localhost:5000/api/v1/business/getone/BUSINESS_ID'
```

### Update Business
```shell
curl --location --request PATCH 'http://localhost:5000/api/v1/business/patch/BUSINESS_ID' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Updated Business Name",
    "location": "Updated Location",
    "businessType": "ecommerce",
    "hospitalityType": "Updated Type",
    "email": "updated@example.com",
    "phoneNumber": "+9876543210"
}'
```

### Get Business Profile
```shell
curl --location 'http://localhost:5000/api/v1/business/profile' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN'
```

## Category Endpoints

### Get All Categories
```shell
curl --location 'http://localhost:5000/api/v1/categories/categories'
```

### Get Category by ID
```shell
curl --location 'http://localhost:5000/api/v1/categories/CATEGORY_ID'
```

### Create Category
```shell
curl --location 'http://localhost:5000/api/v1/categories/create' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--data '{
    "name": "Category Name",
    "description": "Category Description"
}'
```

### Update Category
```shell
curl --location --request PATCH 'http://localhost:5000/api/v1/categories/patch/CATEGORY_ID' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--data '{
    "name": "Updated Category Name",
    "description": "Updated Category Description"
}'
```

## Product Endpoints

### Create Product
```shell
curl --location 'http://localhost:5000/api/v1/products/create' \
--header 'Content-Type: multipart/form-data' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--form 'name="Product Name"' \
--form 'description="Product Description"' \
--form 'category="Category Name"' \
--form 'stock="100"' \
--form 'price="99.99"' \
--form 'businessName="Business Name"' \
--form 'media=@"/path/to/image.jpg"'
```

### Get Product by ID
```shell
curl --location 'http://localhost:5000/api/v1/products/getone/PRODUCT_ID'
```

### Get All Products
```shell
curl --location 'http://localhost:5000/api/v1/products/getall'
```

### Update Product
```shell
curl --location --request PATCH 'http://localhost:5000/api/v1/products/patch/PRODUCT_ID' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_JWT_TOKEN' \
--data '{
    "name": "Updated Product Name",
    "description": "Updated Product Description",
    "category": "Category Name",
    "stock": 150,
    "price": 129.99,
    "rating": 4.5
}'
```

### Get Products with Pagination
```shell
curl --location 'http://localhost:5000/api/v1/products/products?page=1&per_page=10&category=CATEGORY_ID'
```

## AI-Powered Product Search Endpoints

### LangChain Query
```shell
curl --location 'http://localhost:5000/api/v1/products/langchain/query' \
--header 'Content-Type: application/json' \
--data '{
    "query": "Show me headphones"
}'
```

### Query Products (Basic NLP)
```shell
curl --location 'http://localhost:5000/api/v1/products/query-products' \
--header 'Content-Type: application/json' \
--data '{
    "message": "I need a smartphone with good camera"
}'
```

### Single Comprehensive Query (Enhanced NLP)
```shell
curl --location 'http://localhost:5000/api/v1/products/nlp_search/products' \
--header 'Content-Type: application/json' \
--data '{
    "message": "I want a tv and headphones below kes 1000"
}'
```

### Multiple Query Interpretations (Advanced NLP)
```shell
curl --location 'http://localhost:5000/api/v1/products/nlp_search/products/multiple' \
--header 'Content-Type: application/json' \
--data '{
    "message": "I want a tv and headphones below kes 1000"
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
