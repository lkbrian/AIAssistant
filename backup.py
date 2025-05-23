from config import db
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import check_password_hash, generate_password_hash
import json

import cohere
import requests
from flask import current_app
from sqlalchemy import text


def generate_embedding(text):
    """Generate embedding using Cohere API"""
    try:
        co = cohere.Client(api_key=current_app.config["COHERE_API_KEY"])
        response = co.embed(texts=[text], model=current_app.config["EMBEDDING_MODEL"])
        return response.embeddings[0]
    except Exception as e:
        current_app.logger.error(f"Error generating embedding: {str(e)}")
        return None


def query_groq(message):
    """Query GROQ API for natural language processing and SQL generation"""
    try:
        api_key = current_app.config["GROQ_API_KEY"]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        system_prompt = """
        You are a helpful shopping assistant for an e-commerce store. 
        Your task is to:
        1. Respond naturally to the user's query about products
        2. Convert product search requests into PostgreSQL queries
        
        The database has a 'products' table with these columns:
        - id (integer)
        - name (text)
        - description (text)
        - price (float)
        - category (integer, foreign key to categories.id)
        - stock (integer)
        - image_url (text)
        - rating (float)
        - embedding (vector)
        - created_at (timestamp)
        - updated_at (timestamp)
        
        There's also a 'categories' table with:
        - id (integer)
        - name (text)
        - description (text)
        
        For product searches:
        - Return a natural language response to the user
        - Generate a PostgreSQL query that searches for relevant products
        - Use ILIKE for text matching (case insensitive)
        - Join with categories table when needed
        
        Return your response in JSON format with two fields:
        - 'response': Your natural language response to the user
        - 'sql_query': The PostgreSQL query to find matching products
        """

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "model": "llama3-70b-8192",
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse the content to extract response and SQL query
            # This is a simplified parsing - in production you'd want more robust parsing
            try:
                parsed = json.loads(content)
                return {
                    "response": parsed.get("response", ""),
                    "sql_query": parsed.get("sql_query", ""),
                }
            except:
                # Fallback if parsing fails
                return {
                    "response": "I'm sorry, I couldn't process your request properly.",
                    "sql_query": "SELECT * FROM products LIMIT 5",
                }
        else:
            current_app.logger.error(
                f"GROQ API error: {response.status_code} - {response.text}"
            )
            return {
                "response": "I'm sorry, I encountered an error processing your request.",
                "sql_query": "SELECT * FROM products LIMIT 5",
            }
    except Exception as e:
        current_app.logger.error(f"Error querying GROQ: {str(e)}")
        return {
            "response": "I'm sorry, I encountered an error processing your request.",
            "sql_query": "SELECT * FROM products LIMIT 5",
        }


def get_groq_response(message):
    """
    Enhanced GROQ API function for sophisticated product search with SQL query generation.
    Generates a single comprehensive query that searches across all relevant fields.
    """
    try:
        api_key = current_app.config["GROQ_API_KEY"]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        system_prompt = """
        You are a highly intelligent and helpful AI shopping assistant integrated with a PostgreSQL product catalog. Your job is to understand user queries and help them find the right products by providing natural language responses and generating a comprehensive SQL query.

        IMPORTANT: You MUST respond in valid JSON format with the exact structure shown at the end. No text outside this JSON structure.

        ---

        📊 Database Schema:

        Table: products  
        - id (int)  
        - name (text)  
        - description (text)  
        - price (numeric)  
        - rating (numeric)  
        - category (int, foreign key to categories.id)
        - stock (integer)
        - image_url (text)

        Table: categories  
        - id (int)  
        - name (text)
        - description (text)

        ---

        🧠 Core Behaviors:

        1. **Understand User Intent Comprehensively**  
        - Interpret casual, vague, or detailed queries thoughtfully
        - Infer implied meanings beyond keywords:
            - "cheap" → price is low (e.g., price < 50)
            - "affordable" → moderate price (e.g., price < 100)
            - "expensive" → high price (e.g., price > 200)
            - "best" → high rating (e.g., rating > 4)
            - "cool/nice" → positive description match

        2. **Respond Conversationally**  
        - Start with a friendly, helpful message that shows you understood
        - Summarize what you're returning without asking for clarification

        3. **Generate ONE SQL Query That Searches ALL Relevant Fields**
        - ALWAYS use EXACTLY this SELECT clause format:
            SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name
        - ALWAYS use JOIN with categories table:
            FROM products p JOIN categories c ON p.category = c.id
        - ALWAYS search across ALL these fields using OR conditions:
            (p.name ILIKE '%keyword%' OR p.description ILIKE '%keyword%' OR c.name ILIKE '%keyword%' OR c.description ILIKE '%keyword%')
        - Apply appropriate filters based on user intent (price, rating, etc.)
        - Use appropriate ORDER BY based on user intent
        - ALWAYS include LIMIT 10 at the end

        ---

        ⚠️ Technical Requirements:

        - Query must be PostgreSQL compatible
        - Always use proper SQL syntax with quotes around text values
        - Limit results to a reasonable number (5-10 items)
        - Ensure all SQL is injection-safe (no user input directly in SQL)
        - Return EXACTLY this JSON structure:

        {
        "response": "Your friendly explanation here",
        "query": "SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id WHERE ... ORDER BY ... LIMIT 10;"
        }
        """

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "model": "llama3-70b-8192",
            "temperature": 0,  # Lower temperature for more consistent responses
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            current_app.logger.info(f"GROQ raw response: {content[:300]}...")

            # Try to parse as JSON
            try:
                # First, try direct JSON parsing
                parsed = json.loads(content)

                # Ensure we have the required fields
                if "response" not in parsed:
                    parsed["response"] = (
                        "Here are some products that might interest you."
                    )

                if "query" not in parsed:
                    # Default query if none provided
                    parsed["query"] = (
                        "SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 10;"
                    )

                # For backward compatibility
                parsed["sql_query"] = parsed["query"]
                parsed["queries"] = [parsed["query"]]

                return parsed

            except json.JSONDecodeError:
                current_app.logger.warning(
                    f"Failed to parse response as JSON, attempting to extract structured data from text: {content}"
                )

                # Extract response text (first paragraph)
                response_text = content.split("\n\n")[0].strip()

                # Try to extract SQL query using multiple regex patterns
                import re

                # Pattern 1: Look for a complete SELECT statement with specific columns
                sql_query_match = re.search(
                    r"SELECT\s+p\.id,\s*p\.name.*?LIMIT\s+\d+\s*;?",
                    content,
                    re.IGNORECASE | re.DOTALL,
                )

                # Pattern 2: Look for any SELECT statement
                if not sql_query_match:
                    sql_query_match = re.search(
                        r"SELECT\s+.*?FROM\s+products.*?LIMIT\s+\d+\s*;?",
                        content,
                        re.IGNORECASE | re.DOTALL,
                    )

                # Pattern 3: Look for code blocks that might contain SQL
                if not sql_query_match:
                    code_blocks = re.findall(r"```(?:sql)?(.*?)```", content, re.DOTALL)
                    for block in code_blocks:
                        if "SELECT" in block.upper() and "FROM" in block.upper():
                            sql_query_match = re.search(
                                r"SELECT\s+.*?LIMIT\s+\d+\s*;?",
                                block,
                                re.IGNORECASE | re.DOTALL,
                            )
                            if sql_query_match:
                                break

                if sql_query_match:
                    query = sql_query_match.group(0).strip()
                    # Ensure the query ends with a semicolon
                    if not query.endswith(";"):
                        query += ";"
                else:
                    # If no specific query found, generate a query based on the message
                    keywords = message.lower().split()
                    search_terms = []
                    price_filter = ""

                    # Extract potential price constraints
                    price_keywords = [
                        "below",
                        "under",
                        "less",
                        "cheaper",
                        "max",
                        "maximum",
                    ]
                    price_value = None

                    for i, word in enumerate(keywords):
                        if word in price_keywords and i < len(keywords) - 1:
                            try:
                                # Try to extract a numeric value after a price keyword
                                next_word = (
                                    keywords[i + 1]
                                    .replace("kes", "")
                                    .replace("$", "")
                                    .strip()
                                )
                                price_value = float(next_word)
                                price_filter = f"p.price < {price_value}"
                            except (ValueError, IndexError):
                                pass

                    # Extract search terms (words longer than 3 chars that aren't price-related)
                    for word in keywords:
                        if (
                            len(word) > 3
                            and word not in price_keywords
                            and not word.replace(".", "").isdigit()
                        ):
                            search_terms.append(word)

                    # Build search conditions
                    search_conditions = []
                    for term in search_terms:
                        term = term.replace("'", "''")  # Escape single quotes
                        search_conditions.append(
                            f"(p.name ILIKE '%{term}%' OR p.description ILIKE '%{term}%' OR c.name ILIKE '%{term}%' OR c.description ILIKE '%{term}%')"
                        )

                    # Combine conditions
                    where_clause = " OR ".join(search_conditions)
                    if price_filter and where_clause:
                        where_clause = f"({where_clause}) AND {price_filter}"
                    elif price_filter:
                        where_clause = price_filter
                    elif not where_clause:
                        where_clause = "1=1"  # Default condition if no search terms

                    # Generate the query
                    query = f"SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id WHERE {where_clause} ORDER BY p.rating DESC LIMIT 10;"

                # Generate a response if we couldn't extract one
                if not response_text or len(response_text) < 20:
                    if price_filter:
                        response_text = f"Here are some products matching your search with prices {price_filter.replace('p.price', '')}."
                    else:
                        response_text = (
                            "Here are some products that might match your search."
                        )

                return {
                    "response": response_text,
                    "query": query,
                    "sql_query": query,  # For backward compatibility
                    "queries": [query],  # For backward compatibility
                }
        else:
            current_app.logger.error(
                f"GROQ API error: {response.status_code} - {response.text}"
            )
            return {
                "response": "I'm sorry, I encountered an error processing your request.",
                "query": "SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 10;",
                "sql_query": "SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 10;",
                "queries": [
                    "SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 10;"
                ],
            }
    except Exception as e:
        current_app.logger.error(f"Error in get_groq_response: {str(e)}")
        return {
            "response": "I'm sorry, I encountered an error processing your request.",
            "query": "SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 10;",
            "sql_query": "SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 10;",
            "queries": [
                "SELECT p.id, p.name,p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 10;"
            ],
        }


def search_products_by_embedding(query_text, limit=10):
    """
    Search products by semantic similarity using embeddings.

    Args:
        query_text: The text to search for
        limit: Maximum number of results to return

    Returns:
        List of products sorted by similarity to the query
    """
    try:
        # Generate embedding for the query text
        query_embedding = generate_embedding(query_text)

        if not query_embedding:
            current_app.logger.error("Failed to generate embedding for query")
            return []

        # Convert embedding to PostgreSQL array format
        embedding_array = f"'{{{','.join(str(x) for x in query_embedding)}}}'"

        # Use L2 distance (Euclidean distance) instead of cosine similarity
        # This is more commonly supported without special extensions
        sql_query = f"""
        SELECT 
            p.id, p.name, p.description, p.price, p.rating, c.name AS category_name
        FROM 
            products p
        JOIN
            categories c ON p.category = c.id
        WHERE 
            p.embedding IS NOT NULL
        ORDER BY 
            p.embedding <-> {embedding_array}::vector
        LIMIT {limit}
        """

        # Execute the query
        result = db.session.execute(text(sql_query))

        # Convert result to list of dictionaries
        products = []
        for row in result:
            product = {}
            for column, value in row._mapping.items():
                product[column] = value
            products.append(product)

        return products
    except Exception as e:
        current_app.logger.error(f"Error searching products by embedding: {str(e)}")

        # Fallback to keyword search if vector search fails
        try:
            current_app.logger.info(f"Falling back to keyword search for: {query_text}")
            # Simple keyword search as fallback
            words = query_text.split()
            conditions = []

            for word in words:
                if len(word) > 3:  # Only use words longer than 3 chars
                    word = word.replace("'", "''")  # Escape single quotes
                    conditions.append(
                        f"p.name ILIKE '%{word}%' OR p.description ILIKE '%{word}%'"
                    )

            where_clause = " OR ".join(conditions) if conditions else "1=1"

            sql_query = f"""
            SELECT 
                p.id, p.name, p.description, p.price, p.rating, c.name AS category_name
            FROM 
                products p
            JOIN
                categories c ON p.category = c.id
            WHERE 
                {where_clause}
            ORDER BY 
                p.rating DESC
            LIMIT {limit}
            """

            result = db.session.execute(text(sql_query))

            products = []
            for row in result:
                product = {}
                for column, value in row._mapping.items():
                    product[column] = value
                products.append(product)

            return products

        except Exception as fallback_error:
            current_app.logger.error(
                f"Fallback search also failed: {str(fallback_error)}"
            )
            return []


def get_groq_response_multiple_queries(message):
    """
    Enhanced GROQ API function for sophisticated product search with SQL query generation.
    Handles both structured JSON responses and unstructured text responses.
    """
    try:
        api_key = current_app.config["GROQ_API_KEY"]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        system_prompt = """
        You are a highly intelligent and helpful AI shopping assistant integrated with a PostgreSQL product catalog. Your job is to understand user queries and help them find the right products by providing natural language responses and generating comprehensive SQL queries.

        IMPORTANT: You MUST respond in valid JSON format with the exact structure shown at the end. No text outside this JSON structure.

        ---

        📊 Database Schema:

        Table: products  
        - id (int)  
        - name (text)  
        - description (text)  
        - price (numeric)  
        - rating (numeric)  
        - category (int, foreign key to categories.id)
        - stock (integer)
        - image_url (text)

        Table: categories  
        - id (int)  
        - name (text)
        - description (text)

        ---

        🧠 Core Behaviors:

        1. **Understand User Intent Comprehensively**  
        - Interpret casual, vague, or detailed queries thoughtfully
        - Infer implied meanings beyond keywords:
            - "cheap" → price is low
            - "best" → high rating
            - "cool/nice" → positive description match
            - "gift ideas" → appropriate gift categories

        2. **Respond Conversationally**  
        - Start with a friendly, helpful message that shows you understood
        - Summarize what you're returning without asking for clarification

        3. **Generate Two SQL Queries That Search ALL Relevant Fields**
        - ALWAYS search across MULTIPLE fields:
            - Product names (p.name)
            - Product descriptions (p.description)
            - Category names (c.name)
            - Category descriptions (c.description)
        - First query: Most likely interpretation of user intent
        - Second query: Alternative interpretation or broader/narrower scope
        - Both must be SELECT-only and safe
        - ALWAYS use JOINs with categories table
        - ALWAYS use ILIKE for case-insensitive matching
        - Apply appropriate filters and sorting

        4. **Handle Vague Requests**
        - For unclear queries, return general product recommendations
        - First query: Sort by rating (best products)
        - Second query: Different approach (newest, popular, etc.)

        ---

        ⚠️ Technical Requirements:

        - All queries must be PostgreSQL compatible
        - Always use proper SQL syntax with quotes around text values
        - Limit results to a reasonable number (5-10 items)
        - Ensure all SQL is injection-safe (no user input directly in SQL)
        - ALWAYS include JOIN with categories table
        - ALWAYS search across product name, product description, category name, and category description
        - Use OR conditions to match any of these fields
        - Return EXACTLY this JSON structure:

        {
        "response": "Your friendly explanation here",
        "queries": [
            "SQL query #1 (primary interpretation)",
            "SQL query #2 (alternative interpretation)"
        ]
        }
        """

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "model": "llama3-70b-8192",
            "temperature": 0,  # Lower temperature for more consistent responses
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            current_app.logger.info(f"GROQ raw response: {content[:100]}...")

            # Try to parse as JSON
            try:
                # First, try direct JSON parsing
                parsed = json.loads(content)

                # Ensure we have the required fields
                if "response" not in parsed:
                    parsed["response"] = (
                        "Here are some products that might interest you."
                    )

                if "queries" not in parsed:
                    # If we have a single query field, use that
                    if "sql_query" in parsed:
                        parsed["queries"] = [parsed["sql_query"]]
                    else:
                        parsed["queries"] = [
                            "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"
                        ]

                # If queries is provided but empty, add a default query
                if not parsed["queries"]:
                    parsed["queries"] = [
                        "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"
                    ]

                # Ensure we have at least 2 queries
                if len(parsed["queries"]) == 1:
                    parsed["queries"].append(
                        "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5"
                    )

                # For backward compatibility
                parsed["sql_query"] = parsed["queries"][0]

                return parsed

            except json.JSONDecodeError:
                current_app.logger.warning(
                    "Failed to parse response as JSON, attempting to extract structured data from text"
                )

                # Extract response text (first paragraph)
                response_text = content.split("\n\n")[0].strip()

                # Try to extract SQL queries using regex
                import re

                sql_queries = re.findall(
                    r"SELECT\s+.*?;", content, re.IGNORECASE | re.DOTALL
                )

                # If no queries found with semicolons, try without
                if not sql_queries:
                    sql_queries = re.findall(
                        r"SELECT\s+.*?FROM\s+.*?(?:WHERE|ORDER BY|LIMIT|$)",
                        content,
                        re.IGNORECASE | re.DOTALL,
                    )

                # Clean up the queries
                clean_queries = []
                for query in sql_queries:
                    # Remove any markdown code formatting
                    query = re.sub(r"```sql|```", "", query).strip()
                    clean_queries.append(query)

                # If still no queries found, use default
                if not clean_queries:
                    clean_queries = [
                        "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"
                    ]

                # Ensure we have at least 2 queries
                if len(clean_queries) == 1:
                    clean_queries.append(
                        "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5"
                    )

                return {
                    "response": response_text,
                    "queries": clean_queries,
                    "sql_query": clean_queries[0],  # For backward compatibility
                }
        else:
            current_app.logger.error(
                f"GROQ API error: {response.status_code} - {response.text}"
            )
            return {
                "response": "I'm sorry, I encountered an error processing your request.",
                "queries": [
                    "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5",
                    "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5",
                ],
                "sql_query": "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5",
            }
    except Exception as e:
        current_app.logger.error(f"Error in get_groq_response: {str(e)}")

        return {
            "response": "I'm sorry, I encountered an error processing your request.",
            "queries": [
                "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5",
                "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5",
            ],
            "sql_query": "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5",
        }
    except Exception as e:
        current_app.logger.error(f"Error in get_groq_response: {str(e)}")
        return {
            "response": "I'm sorry, I encountered an error processing your request.",
            "queries": [
                "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5",
                "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5",
            ],
            "sql_query": "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5",
        }


def execute_product_query(sql_query):
    """Execute the SQL query against the database with proper sanitization"""
    try:
        # Execute the query
        result = db.session.execute(text(sql_query))

        # Convert result to list of dictionaries
        products = []
        for row in result:
            product = {}
            for column, value in row._mapping.items():
                product[column] = value
            products.append(product)

        return products
    except Exception as e:
        current_app.logger.error(f"Error executing query: {str(e)}")
        return []


def sanitize_sql_query(sql_query):
    """Basic SQL sanitization to prevent injection"""
    # This is a very basic sanitization - in production you'd want more robust protection
    disallowed_keywords = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
    ]

    for keyword in disallowed_keywords:
        if keyword in sql_query.upper():
            return "SELECT * FROM products LIMIT 5"

    return sql_query


class ModelsBackup:
    class User(db.Model, SerializerMixin):
        __tablename__ = "users"

        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(256), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(
            db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        )

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

        def to_dict(self):
            return {
                "id": self.id,
                "username": self.username,
                "email": self.email,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
            }

    class Category(db.Model, SerializerMixin):
        __tablename__ = "categories"
        serialize_only = ("id", "name", "description", "created_at", "updated_at")

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        description = db.Column(db.Text)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(
            db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        )

        # Relationship
        products = db.relationship("Product", backref="category_rel", lazy=True)

    class Product(db.Model):
        __tablename__ = "products"
        serialize_only = (
            "id",
            "name",
            "description",
            "price",
            "category",
            "stock",
            "image_url",
            "rating",
            "created_at",
            "updated_at",
        )

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(200), nullable=False)
        description = db.Column(db.Text)
        price = db.Column(db.Float, nullable=False)
        category = db.Column(db.Integer, db.ForeignKey("categories.id"))
        stock = db.Column(db.Integer, default=0)
        image_url = db.Column(db.String(500))
        rating = db.Column(db.Float, default=0)
        embedding = db.Column(ARRAY(FLOAT))
        created_at = db.Column(db.DateTime, server_default=func.now())
        updated_at = db.Column(
            db.DateTime, server_default=func.now(), onupdate=func.now()
        )

        # Relationship
        images = db.relationship(
            "ProductImage", backref="product", lazy=True, cascade="all, delete-orphan"
        )

        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "price": self.price,
                "category": self.category,
                "category_name": self.category_rel.name if self.category_rel else None,
                "stock": self.stock,
                "image_url": self.image_url,
                "rating": self.rating,
                "images": [image.url for image in self.images],
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
            }

    class ProductImage(db.Model):
        __tablename__ = "product_images"

        id = db.Column(db.Integer, primary_key=True)
        product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
        url = db.Column(db.String(500), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        def to_dict(self):
            return {
                "id": self.id,
                "product_id": self.product_id,
                "url": self.url,
                "created_at": self.created_at.isoformat(),
            }


"""-- -- Create extension if not exists
-- CREATE EXTENSION IF NOT EXISTS vector;

-- -- Insert categories
-- INSERT INTO public.categories (name, description)
-- VALUES 
--   ('Electronics', 'Latest gadgets and electronic devices'),
--   ('Footwear', 'Comfortable and stylish shoes'),
--   ('Apparel', 'Fashion clothing and accessories'),
--   ('Home & Living', 'Home decor and furniture'),
--   ('Sports & Fitness', 'Sports equipment and fitness gear');

-- -- Insert products
-- INSERT INTO public.products (name, description, price, category, stock, image_url, rating) 
-- VALUES 
--   -- Original demo products
--   ('Wireless Noise-Cancelling Headphones', 'Premium wireless headphones with active noise cancellation', 199.99, 1, 50, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Ultra-Light Running Shoes', 'Lightweight and comfortable running shoes for professional athletes', 89.99, 2, 75, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
--   ('Premium Leather Sneakers', 'Classic leather sneakers with modern design', 129.99, 2, 60, 'https://images.unsplash.com/photo-1549298916-b41d501d3772?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Smart 4K TV', '55-inch 4K Ultra HD Smart TV with HDR', 699.99, 1, 30, 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
--   ('Casual Denim Jacket', 'Classic denim jacket with modern fit', 79.99, 3, 100, 'https://images.unsplash.com/photo-1576871337632-b9aef4c17ab9?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  
--   -- Additional products
--   ('Mechanical Gaming Keyboard', 'RGB mechanical keyboard with custom switches', 149.99, 1, 40, 'https://images.unsplash.com/photo-1511478156903-9aa2c6ac3459?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
--   ('Wireless Gaming Mouse', 'High-precision wireless gaming mouse', 79.99, 1, 45, 'https://images.unsplash.com/photo-1527814050087-3793815479db?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Leather Hiking Boots', 'Waterproof leather hiking boots for outdoor adventures', 159.99, 2, 35, 'https://images.unsplash.com/photo-1520639888713-7851133b1ed0?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
--   ('Smart Watch Series X', 'Advanced smartwatch with health monitoring', 299.99, 1, 55, 'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Premium Yoga Mat', 'Eco-friendly non-slip yoga mat', 49.99, 5, 80, 'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
--   ('Adjustable Dumbbell Set', 'Space-saving adjustable weight dumbbell set', 299.99, 5, 25, 'https://images.unsplash.com/photo-1638536532686-d610adfc8e5c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
--   ('Modern Coffee Table', 'Minimalist wooden coffee table', 199.99, 4, 20, 'https://images.unsplash.com/photo-1532372320572-cda25653a26d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Designer Desk Lamp', 'Adjustable LED desk lamp with wireless charging', 89.99, 4, 40, 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Wool Blend Sweater', 'Comfortable wool blend sweater for winter', 69.99, 3, 65, 'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Premium Backpack', 'Water-resistant laptop backpack with USB charging', 89.99, 3, 50, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
--   ('Wireless Earbuds', 'True wireless earbuds with noise cancellation', 159.99, 1, 70, 'https://images.unsplash.com/photo-1605464315542-bda3e2f4e605?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Smart Home Hub', 'Central control for your smart home devices', 129.99, 1, 35, 'https://images.unsplash.com/photo-1558089687-f282ffcbc126?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
--   ('Fitness Tracker', 'Advanced fitness and sleep tracking device', 79.99, 1, 60, 'https://images.unsplash.com/photo-1576243345690-4e4b79b63288?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4);

-- -- Insert product images for each product
-- INSERT INTO public.product_images (product_id, url)
-- SELECT 
--     id,
--     image_url
-- FROM public.products;

-- First, insert all 12 categories
-- Insert categories (12 total)
INSERT INTO public.categories (name, description) VALUES
  ('Electronics', 'Latest gadgets and electronic devices'),
  ('Footwear', 'Comfortable and stylish shoes'),
  ('Apparel', 'Fashion clothing and accessories'),
  ('Home & Living', 'Home decor and furniture'),
  ('Sports & Fitness', 'Sports equipment and fitness gear'),
  ('Books & Media', 'Books, e-books and audiobooks'),
  ('Beauty & Personal Care', 'Skincare, cosmetics and grooming'),
  ('Toys & Games', 'Educational toys and family games'),
  ('Groceries', 'Daily essentials and gourmet foods'),
  ('Pet Supplies', 'Food and accessories for your pets'),
  ('Automotive', 'Car accessories and maintenance'),
  ('Office Supplies', 'Stationery and work essentials');

-- Generate 500 products using proper CTE structure
INSERT INTO public.products (name, description, price, category, stock, image_url, rating)
WITH base_products AS (
  SELECT * FROM (VALUES
    -- Base products (4 columns: name, description, price, category)
    ('Wireless Headphones', 'Premium wireless headphones with noise cancellation', 199.99, 1),
    ('Running Shoes', 'Lightweight athletic footwear', 89.99, 2),
    ('Leather Sneakers', 'Classic casual footwear', 129.99, 2),
    ('4K Smart TV', 'Ultra HD television with smart features', 699.99, 1),
    ('Denim Jacket', 'Modern casual outerwear', 79.99, 3),
    ('Gaming Keyboard', 'Mechanical RGB keyboard', 149.99, 1),
    ('Wireless Mouse', 'High-precision computer accessory', 79.99, 1),
    ('Hiking Boots', 'Outdoor waterproof footwear', 159.99, 2),
    ('Smart Watch', 'Advanced health monitoring device', 299.99, 1),
    ('Yoga Mat', 'Eco-friendly exercise equipment', 49.99, 5),
    ('Dumbbell Set', 'Adjustable weight system', 299.99, 5),
    ('Coffee Table', 'Modern living room furniture', 199.99, 4),
    ('Desk Lamp', 'Adjustable LED lighting', 89.99, 4),
    ('Wool Sweater', 'Winter clothing essential', 69.99, 3),
    ('Laptop Backpack', 'Durable carrying solution', 89.99, 3),
    ('Wireless Earbuds', 'True wireless audio devices', 159.99, 1),
    ('Smart Home Hub', 'Connected home controller', 129.99, 1),
    ('Fitness Tracker', 'Activity monitoring wearable', 79.99, 1),
    ('Face Cream', 'Anti-aging skincare product', 29.99, 7),
    ('Dog Collar', 'GPS enabled pet accessory', 79.99, 10),
    ('Car Mount', 'Vehicle phone holder', 19.99, 11),
    ('Coffee Beans', 'Premium roasted beans', 14.99, 9),
    ('Board Game', 'Family entertainment package', 39.99, 8),
    ('Yoga Blocks', 'Exercise support equipment', 24.99, 5)
  ) AS t(name, description, price, category)
)
SELECT
  CONCAT(
    split_part(bp.name, ' ', 1),
    ' ',
    CASE 
      WHEN bp.category IN (1,11) THEN (ARRAY['Pro','Smart','Elite'])[floor(random()*3)+1]
      WHEN bp.category IN (2,3,7) THEN (ARRAY['Premium','Luxury','Designer'])[floor(random()*3)+1]
      ELSE ''
    END,
    ' ',
    split_part(bp.name, ' ', 2),
    ' ',
    (ARRAY['X','2024','Edition'])[floor(random()*3)+1]
  ) AS name,

  CONCAT(
    bp.description,
    CASE WHEN random() < 0.4 THEN ' with ' || (ARRAY['advanced features','eco-friendly materials'])[floor(random()*2)+1] ELSE '' END
  ) AS description,

  (bp.price * (0.8 + random()*0.4))::numeric(10,2) AS price,
  bp.category,
  (random()*90 + 10)::int AS stock,
  CASE bp.category
    WHEN 1 THEN 'https://source.unsplash.com/400x400/?electronics'
    WHEN 2 THEN 'https://source.unsplash.com/400x400/?shoes'
    WHEN 3 THEN 'https://source.unsplash.com/400x400/?fashion'
    WHEN 4 THEN 'https://source.unsplash.com/400x400/?furniture'
    WHEN 5 THEN 'https://source.unsplash.com/400x400/?fitness'
    WHEN 6 THEN 'https://source.unsplash.com/400x400/?books'
    WHEN 7 THEN 'https://source.unsplash.com/400x400/?cosmetics'
    WHEN 8 THEN 'https://source.unsplash.com/400x400/?toys'
    WHEN 9 THEN 'https://source.unsplash.com/400x400/?groceries'
    WHEN 10 THEN 'https://source.unsplash.com/400x400/?pets'
    WHEN 11 THEN 'https://source.unsplash.com/400x400/?automotive'
    WHEN 12 THEN 'https://source.unsplash.com/400x400/?office'
  END || '?v=' || floor(random()*1000) AS image_url,
  (4.0 + random()*1.0)::numeric(2,1) AS rating
FROM base_products bp, generate_series(1, 20);

-- Insert product images
INSERT INTO public.product_images (product_id, url)
SELECT id, image_url FROM public.products;
"""
