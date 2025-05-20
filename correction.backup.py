
def get_groq_response(message):
    """
    Enhanced GROQ API function for sophisticated product search with SQL query generation.
    Handles both structured JSON responses and unstructured text responses.
    """
    try:
        api_key = current_app.config['GROQ_API_KEY']
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
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
                {"role": "user", "content": message}
            ],
            "model": "llama3-70b-8192",
            "temperature": 0.2  # Lower temperature for more consistent responses
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                headers=headers, 
                                json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            current_app.logger.info(f"GROQ raw response: {content[:100]}...")
            
            # Try to parse as JSON
            try:
                # First, try direct JSON parsing
                parsed = json.loads(content)
                
                # Ensure we have the required fields
                if 'response' not in parsed:
                    parsed['response'] = "Here are some products that might interest you."
                
                if 'queries' not in parsed:
                    # If we have a single query field, use that
                    if 'sql_query' in parsed:
                        parsed['queries'] = [parsed['sql_query']]
                    else:
                        parsed['queries'] = ["SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"]
                
                # If queries is provided but empty, add a default query
                if not parsed['queries']:
                    parsed['queries'] = ["SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"]
                
                # Ensure we have at least 2 queries
                if len(parsed['queries']) == 1:
                    parsed['queries'].append("SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5")
                
                # For backward compatibility
                parsed['sql_query'] = parsed['queries'][0]
                
                return parsed
                
            except json.JSONDecodeError:
                current_app.logger.warning(f"Failed to parse response as JSON, attempting to extract structured data from text")
                
                # Extract response text (first paragraph)
                response_text = content.split('\n\n')[0].strip()
                
                # Try to extract SQL queries using regex
                import re
                sql_queries = re.findall(r'SELECT\s+.*?;', content, re.IGNORECASE | re.DOTALL)
                
                # If no queries found with semicolons, try without
                if not sql_queries:
                    sql_queries = re.findall(r'SELECT\s+.*?FROM\s+.*?(?:WHERE|ORDER BY|LIMIT|$)', content, re.IGNORECASE | re.DOTALL)
                
                # Clean up the queries
                clean_queries = []
                for query in sql_queries:
                    # Remove any markdown code formatting
                    query = re.sub(r'```sql|```', '', query).strip()
                    clean_queries.append(query)
                
                # If still no queries found, use default
                if not clean_queries:
                    clean_queries = ["SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"]
                
                # Ensure we have at least 2 queries
                if len(clean_queries) == 1:
                    clean_queries.append("SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5")
                
                return {
                    'response': response_text,
                    'queries': clean_queries,
                    'sql_query': clean_queries[0]  # For backward compatibility
                }
        else:
            current_app.logger.error(f"GROQ API error: {response.status_code} - {response.text}")
            return {
                'response': "I'm sorry, I encountered an error processing your request.",
                'queries': ["SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5", 
                           "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5"],
                'sql_query': "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"
            }
    except Exception as e:
        current_app.logger.error(f"Error in get_groq_response: {str(e)}")
    
        return {
                'response': "I'm sorry, I encountered an error processing your request.",
                'queries': ["SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5", 
                           "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5"],
                'sql_query': "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"
            }
    except Exception as e:
        current_app.logger.error(f"Error in get_groq_response: {str(e)}")
        return {
            'response': "I'm sorry, I encountered an error processing your request.",
            'queries': ["SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5",
                       "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.created_at DESC LIMIT 5"],
            'sql_query': "SELECT p.* FROM products p JOIN categories c ON p.category = c.id ORDER BY p.rating DESC LIMIT 5"
        }
