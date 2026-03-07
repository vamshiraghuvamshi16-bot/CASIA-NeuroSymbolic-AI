# app/config.py
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Runtime configuration
LLM_MODE = os.getenv("LLM_MODE", "groq")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-70b-versatile")

# Optional: expose keys if other modules need them
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
