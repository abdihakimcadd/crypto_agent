# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Groq (OpenAI-compatible endpoint)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Pipeline config
SYMBOLS_TABLE = "symbols"
VOLUME_SNAPSHOT = "volume_snapshot"
INDICATOR_SNAPSHOT = "indicator_snapshot"
RESEARCH_OUTPUT = "research_output"
CANDLE_DATA = "candle_data"

# Thresholds
VOLUME_SPIKE_THRESHOLD = 100
ONCHAIN_USD_THRESHOLD = 100_000

# For knowledge base (optional)
MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
