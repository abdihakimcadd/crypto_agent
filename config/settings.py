import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pipeline config
SYMBOLS_TABLE = "symbols"
VOLUME_SNAPSHOT = "volume_snapshot"
INDICATOR_SNAPSHOT = "indicator_snapshot"
RESEARCH_OUTPUT = "research_output"
CANDLE_DATA = "candle_data"

# Thresholds
VOLUME_SPIKE_THRESHOLD = 100  # pct
ONCHAIN_USD_THRESHOLD = 100_000

# For knowledge base (optional)
MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
