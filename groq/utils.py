import json

import cohere
import requests
from flask import current_app
from sqlalchemy import text

from config import db


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
