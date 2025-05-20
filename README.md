# MarketAI Backend

A containerized Flask backend with PostgreSQL database for the MarketAI assistant project.

## Features

- Flask API backend with RESTful endpoints
- PostgreSQL database with pgvector extension for vector operations
- Docker and Docker Compose for easy deployment
- JWT authentication for secure API access
- Product search via natural language queries using GROQ API
- Vector embeddings for products using Cohere API
- CRUD operations for products and categories

## Architecture

- **Framework**: Flask with Flask-RESTful for API endpoints
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Containerization**: Docker and Docker Compose for deployment

## Database Schema

- **products**: id, name, description, price, category, stock, image_url, rating, embedding, created_at, updated_at
- **product_images**: id, product_id, url, created_at
- **categories**: id, name, description, created_at, updated_at
- **users**: id, username, email, password_hash, created_at, updated_at

single comprehensive query
```shell
  curl --location 'http://localhost:5000/api/v1/groq/nlp_search/products' \
  --header 'Content-Type: application/json' \
  --data '{
      "message": "I want a tv and headphones below kes 1000"
  }'
  ```

- `POST /api/v1/groq/nlp_search/products/multiple`: Search products using natural language with multiple query interpretations
```shell
  curl --location 'http://localhost:5000/api/v1/groq/nlp_search/products/multiple' \
  --header 'Content-Type: application/json' \
  --data '{
      "message": "I want a tv and headphones below kes 1000"
  }'
  ```

- `POST /api/v1/groq/products/semantic-search`: Search products by semantic similarity using embeddings
```shell
  curl --location 'http://localhost:5000/api/v1/groq/products/semantic-search' \
  --header 'Content-Type: application/json' \
  --data '{
      "query": "comfortable headphones for long listening sessions",
      "limit": 5
  }'
  ```

- `POST /api/v1/groq/generate-embedding`: Generate embedding for text
```shell
  curl --location 'http://localhost:5000/api/v1/groq/generate-embedding' \
  --header 'Content-Type: application/json' \
  --data '{
      "text": "High-performance smartphone with excellent camera quality"
  }'
  ```

- `GET /api/v1/groq/generate-embeddings/all`: Generate embeddings for all products that don't have them
```shell
  curl --location 'http://localhost:5000/api/v1/groq/generate-embeddings/all' \
  --header 'Authorization: Bearer YOUR_JWT_TOKEN'
  ```

## Setup and Installation

1. Clone the repository and create a virtual environment 
```shell
   python3 -m venv .venv
   pip install -r requirments.txt
```

2. Create a `.env` file with the following variables or check the .env.example
```js
   COHERE_API_KEY=your_cohere_api_key
   GROQ_API_KEY=your_groq_api_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ```
3. Run the application with Docker Compose:
```
   docker compose up -d
   ```

## Development

4. For development with hot-reloading:

```shell
docker compose up
```

## Database Initialization

The database will be automatically initialized with the required tables and extensions when the application starts. To seed the database with initial data, you can use the provided SQL script:

```shell
docker cp seed.sql $(docker compose ps -q db):/seed.sql
docker compose exec db psql -U postgres -d marketai -f /seed.sql
```

confirm the database for tables and seeded data
 - access the database 
 ```shell
 docker compose exec db psql -U postgres -d marketai
 ```
 - check tables 
 ```shell
 \dt
 select * from products;
 ```

Note: don't create vector embedings

