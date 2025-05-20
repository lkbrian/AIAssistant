import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-secret-key')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/marketai')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(weeks=1)
    
    # API Keys
    COHERE_API_KEY = os.environ.get('COHERE_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # Embedding model configuration
    EMBEDDING_MODEL = "embed-v4.0"
    EMBEDDING_DIMENSION = 1024  # Dimension of Cohere's embed-english-v4.0 model
