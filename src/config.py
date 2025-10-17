"""
Configuration settings for AI Customer Support System
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Google Sheets Configuration
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    
    # Model Configuration
    DEFAULT_MODEL = "gpt-3.5-turbo"
    EMBEDDING_MODEL = "text-embedding-ada-002"
    
    # Categories
    CATEGORIES = [
        "Account Issues",
        "Billing & Payments", 
        "Technical Support",
        "Feature Requests",
        "Bug Reports",
        "General Inquiry",
        "Security Issues",
        "Performance Problems",
        "Integration Issues",
        "Documentation"
    ]
    
    # Priority Levels
    PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]
    
    # Confidence Threshold
    MIN_CONFIDENCE_THRESHOLD = 0.7
    
    # Vector Store Configuration
    VECTOR_STORE_PATH = "data/vectorstore"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH = "data/knowledge_base"
    SUPPORT_DOCS_PATH = "data/support_docs"
