import getpass
import os

# import sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
from typing import List, Optional, TypedDict
from dotenv import load_dotenv
from flask import current_app
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph
from sqlalchemy import text

from config import db
from langchain.memory import ConversationBufferMemory


load_dotenv()

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
    temperature=0,
)
memory = ConversationBufferMemory(return_messages=True)
# intent_prompt
# intent_chain = intent_prompt | llm | JsonOutputParser()


class GraphState(TypedDict):
    input: str
    history: List[str]
    sql_query: Optional[str]
    natural_response: Optional[str]
    error: Optional[str]
    products: Optional[List[dict]]


class SQLUtils:

    @staticmethod
    def _sanitize_sql_query(sql_query: str) -> str:
        """Basic SQL sanitization to prevent injection and remove unwanted characters."""
        cleaned_query = sql_query.replace("\\", "").replace("/", "")
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
        if any(keyword in cleaned_query.upper() for keyword in disallowed_keywords):
            return "SELECT * FROM products LIMIT 5"
        return re.sub(r"\s+", " ", cleaned_query).strip()

    @staticmethod
    def _execute_product_query(sql_query: str) -> List[dict]:
        """Execute SQL safely using SQLAlchemy, return results as list of dicts."""
        try:
            result = db.session.execute(text(sql_query))

            # Convert result to list of dictionaries
            products = [
                {column: value for column, value in row._mapping.items()}
                for row in result
            ]
            current_app.logger.info(
                f"Executed SQL query successfully. Found {len(products)} products."
            )
            return products
        except Exception as e:
            current_app.logger.error(f"Error executing query: {str(e)}")
            return []


class LLMQueryPipeline:
    def __init__(self, llm, memory, sql_utils):
        self.llm = llm
        self.memory = memory
        self.sql_utils = sql_utils
        self.intent_chain = self._build_intent_chain()
        self.graph = self._build_graph()

    def _build_intent_chain(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Act as an AI shopping assistant with PostgreSQL expertise. Convert queries to JSON with SQL following these rules:
            **Schema:**
            - products (id, name, description, price, rating, category, stock, image_url,created_at, updated_at)
            - categories (id, name, description)
            
            **Semantic analysis:**
            - Carefully analyze the user's input to determine their intent and relevant product filters.
            - Identify if the input is a **greeting**, **question**, **command**, or **product request**.
            - If the input is only a **greeting or small talk** (e.g., "hello", "how are you?"), respond naturally and **do not generate a SQL query**.
            - If the input includes a **product-related intent**, extract and interpret relevant features:

            **Instructions:**
            1. Analyze query for:
            - Price hints: "cheap"→<50, "affordable"→<100, "expensive"→>200
            - Quality hints: "best"→rating>4, "cool/nice"→description match
            2. Respond with friendly message showing understanding
            3. Generate 1 SQL query:
            - SELECT p.*, c.name AS category_name
            - FROM products p JOIN categories c ON p.category=c.id
            - WHERE (p.name ILIKE %s OR p.description ILIKE %s OR c.name ILIKE %s OR c.description ILIKE %s)
            - Add filters/ordering based on intent
            - LIMIT 10

            Return EXACTLY this format:
            {{
            "response": "Friendly response here",
            "query": "The SQL query"
            }}""",
                ),
                MessagesPlaceholder(variable_name="history"),
                ("user", "{input}"),
                ("system", "Only output the SQL query."),
            ]
        )
        return prompt | self.llm | JsonOutputParser()

    def _node_extract_sql(self, state: GraphState) -> dict:
        try:
            user_input = state["input"]
            self.memory.chat_memory.add_user_message(user_input)

            result = self.intent_chain.invoke(
                {
                    "input": user_input,
                    "history": self.memory.load_memory_variables({})["history"],
                }
            )

            if not all(key in result for key in ("response", "query")):
                raise ValueError("Invalid response format from LLM", result)

            self.memory.chat_memory.add_ai_message(f"{result['response']}")
            current_app.logger.info(f"Successfully extracted SQL: {result['query']}")
            return {
                "sql_query": result["query"],
                "natural_response": result["response"],
                "history": self.memory.load_memory_variables({})["history"],
            }

        except Exception as e:
            current_app.logger.error(f"Error during SQL extraction: {str(e)}")
            return {
                "sql_query": None,
                "natural_response": f"Error processing request: {str(e)}",
                "history": state["history"],
            }

    def _node_execute_query(self, state: GraphState) -> GraphState:
        sql_query = state.get("sql_query")
        if not sql_query:
            current_app.logger.warning("No SQL query provided to execute.")
            return {
                **state,
                "error": "No SQL query provided",
                "products": [],
            }

        try:
            safe_query = self.sql_utils._sanitize_sql_query(sql_query)
            products = self.sql_utils._execute_product_query(safe_query)

            return {
                **state,
                "products": products,
            }

        except Exception as e:
            current_app.logger.error(f"Failed to execute SQL query: {str(e)}")
            return {
                **state,
                "error": f"Failed to execute SQL: {str(e)}",
                "products": [],
            }

    def _node_format_output(self, state: GraphState) -> dict:
        if state.get("error"):
            current_app.logger.error(f"Error occurred: {state['error']}")
            return {
                "response": f"Error: {state['error']}",
                "products": None,
            }

        try:
            response = f"{state['natural_response']}\n\nFound {len(state['products'])} matching products:"
            return {
                "response": response,
                "products": state["products"],
                "query": state["sql_query"],
            }
        except Exception as e:
            current_app.logger.error(f"Error formatting results: {str(e)}")
            return {
                "output": {
                    "response": f"Error formatting results: {str(e)}",
                    "products": None,
                }
            }

    def _build_graph(self):
        builder = StateGraph(state_schema=GraphState)
        builder.add_node("extract_sql", self._node_extract_sql)
        builder.add_node("execute_query", self._node_execute_query)
        builder.add_node("format_output", self._node_format_output)
        builder.add_edge("extract_sql", "execute_query")
        builder.add_edge("execute_query", "format_output")
        builder.set_entry_point("extract_sql")
        builder.set_finish_point("format_output")
        return builder.compile()

    def run(self, user_input: str) -> dict:
        initial_state = {
            "input": user_input,
            "history": self.memory.load_memory_variables({})["history"],
        }
        return self.graph.invoke(initial_state)


def run_pipeline(user_input: str) -> dict:
    sql_utils = SQLUtils()
    pipeline = LLMQueryPipeline(llm, memory, sql_utils)
    result = pipeline.run(user_input)

    # Convert result to JSON-serializable format
    serializable_result = {}
    for key, value in result.items():
        if key == "history":
            # Convert message objects to dictionaries
            serializable_result[key] = [
                {
                    "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content,
                }
                for msg in value
            ]
        else:
            serializable_result[key] = value

    return serializable_result
