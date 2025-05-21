import getpass
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import re
from typing import List, Optional, TypedDict

# from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from flask import current_app
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph
from sqlalchemy import text

from config import db, app
from langchain.memory import ConversationBufferMemory


load_dotenv()


class GraphState(TypedDict):
    input: str
    history: List[str]
    sql_query: Optional[str]
    natural_response: Optional[str]
    error: Optional[str]
    products: Optional[List[dict]]


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


def sanitize_sql_query(sql_query: str) -> str:
    """Basic SQL sanitization to prevent injection and remove unwanted characters."""
    # Normalize slashes
    cleaned_query = sql_query.replace("\\", "").replace("/", "")

    # Disallowed SQL keywords
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

    # Check for dangerous keywords
    upper_query = cleaned_query.upper()
    for keyword in disallowed_keywords:
        if keyword in upper_query:
            # Return safe fallback
            return "SELECT * FROM products LIMIT 5"

    # Optionally remove redundant whitespace
    cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()

    return cleaned_query


if not os.getenv("AZURE_OPENAI_API_KEY"):
    os.environ["AZURE_OPENAI_API_KEY"] = getpass.getpass("Enter API key for Azure: ")

endpoint = os.getenv("AZURE_DEPLOYMENT_ENDPOINT", "https://lemu.openai.azure.com/")
api_key = os.getenv("AZURE_API_KEY")
deployment = os.getenv("DEPLOYMENT_NAME", "lemu-gpt-4o-mini")


llm = AzureChatOpenAI(
    azure_endpoint=endpoint,
    deployment_name=deployment,
    api_key=api_key,
    api_version="2025-01-01-preview",
    temperature=0.2,
)
memory = ConversationBufferMemory(return_messages=True)


intent_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Act as an AI shopping assistant with PostgreSQL expertise. Convert queries to JSON with SQL following these rules:

**Schema:**
- products (id, name, description, price, rating, category, stock, image_url)
- categories (id, name, description)

**Instructions:**
1. Analyze query for:
   - Price hints: "cheap"→<50, "affordable"→<100, "expensive"→>200
   - Quality hints: "best"→rating>4, "cool/nice"→description match
2. Respond with friendly message showing understanding
3. Generate 1 SQL query:
   - SELECT p.id, p.name, p.image_url, p.description, p.price, p.rating, c.name AS category_name
   - FROM products p JOIN categories c ON p.category=c.id
   - WHERE (p.name ILIKE %s OR p.description ILIKE %s OR c.name ILIKE %s OR c.description ILIKE %s)
   - Add filters/ordering based on intent
   - LIMIT 10

Return EXACTLY this format:
{{
  "response": "Friendly response here",
  "query": "SELECT p.id, p.name, p.image_url, p.description, p.price, p.rating, c.name AS category_name FROM products p JOIN categories c ON p.category = c.id WHERE ... ORDER BY ... LIMIT 10;"
}}""",
        ),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{input}"),
        ("system", "Only output the SQL query."),
    ]
)

intent_chain = intent_prompt | llm | JsonOutputParser()


# 3. Node function remains similar but uses proper message handling
def node_extract_sql(state: GraphState) -> dict:
    try:
        # Update conversation history
        user_input = state["input"]
        memory.chat_memory.add_user_message(user_input)

        # Generate structured response
        result = intent_chain.invoke(
            {
                "input": user_input,
                "history": memory.load_memory_variables({})["history"],
            }
        )

        # Validate response structure
        if not all(key in result for key in ("response", "query")):
            raise ValueError("Invalid response format from LLM")

        # Update memory and state
        memory.chat_memory.add_ai_message(
            f"Response: {result['response']}\nQuery: {result['query']}"
        )

        return {
            "sql_query": result["query"],
            "natural_response": result["response"],
            "history": state["history"]
            + [HumanMessage(content=user_input), AIMessage(content=result["response"])],
        }

    except Exception as e:
        # Handle errors gracefully
        return {
            "sql_query": None,
            "natural_response": f"Error processing request: {str(e)}",
            "history": state["history"],
        }


def execute_query_node(state: GraphState) -> GraphState:
    sql_query = state.get("sql_query")
    if not sql_query:
        return {
            **state,
            "error": "No SQL query provided",
            "products": [],
        }

    try:
        # Sanitize query
        safe_query = sanitize_sql_query(sql_query)

        # Execute and return products
        products = execute_product_query(safe_query)

        return {
            **state,
            "products": products,
        }

    except Exception as e:
        return {
            **state,
            "error": f"Failed to execute SQL: {str(e)}",
            "products": [],
        }


def format_output_node(state: GraphState) -> dict:
    if state.get("error"):
        return {
            "output": {
                "response": f"Error: {state['error']}",
                "products": None,
            }
        }

    try:
        # Format output
        response = f"{state['natural_response']}\n\nFound {len(state['products'])} matching products:"
        return {
            "output": {
                "response": response,
                "products": state["products"],
                "query": state["sql_query"],
            }
        }
    except Exception as e:
        return {
            "output": {
                "response": f"Error formatting results: {str(e)}",
                "products": None,
            }
        }


builder = StateGraph(state_schema=GraphState)
builder.add_node("extract_sql", node_extract_sql)
builder.add_node("execute_query", execute_query_node)
builder.add_node("format_output", format_output_node)
builder.add_edge("extract_sql", "execute_query")
builder.add_edge("execute_query", "format_output")

builder.set_entry_point("extract_sql")
builder.set_finish_point("format_output")
graph = builder.compile()

# 5. Test the corrected implementation
with app.app_context():
    initial_state = {"input": "Show me a Tv under $1000", "history": []}
    result = graph.invoke(initial_state)

    print(f"🧠 Generated Query: {result}")
    print(result["sql_query"])
