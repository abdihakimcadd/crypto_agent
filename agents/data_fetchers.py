"""
Agents 1-3: pure Python fetchers. No LLM. No volume calculation.
News and on-chain are fetched in-memory only (no DB write).
"""
import asyncio
import aiohttp
from db.supabase_client import supabase

BINANCE_API = "https://api.binance.com/api/v3/klines"
COINGECKO_NEWS = "https://api.coingecko.com/api/v3/news""

# In-memory store for the current pipeline run
_current_run_data = {
    "news": [],
    "onchain": {},
}


# ─── Agent 1 replacement: read-only market data ─────────────────────────────

def get_market_data(symbol: str) -> dict:
    """Read current volume + indicator snapshot for a symbol from Supabase.
    No calculation. No Binance API calls.
    """
    vol_res = supabase.table("volume_snapshot").select("*").eq("symbol", symbol).execute()
    ind_res = supabase.table("indicator_snapshot").select("*").eq("symbol", symbol).execute()

    return {
        "volume": vol_res.data[0] if vol_res.data else {},
        "indicators": ind_res.data[0] if ind_res.data else {},
    }


# ─── Agent 2: news fetcher (in-memory only) ─────────────────────────────────

async def fetch_news() -> list:
    """Fetch latest crypto news from CoinGecko. Returns in-memory list.
    No DB write. No news_items table.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(COINGECKO_NEWS) as resp:
            data = await resp.json()

    items = []
    for item in data.get("data", []):
        items.append({
            "id": item.get("id"),
            "headline": item.get("title"),
            "source": item.get("source", "coingecko"),
            "published_at": item.get("published_at"),
            "url": item.get("url"),
        })

    _current_run_data["news"] = items
    return items


def get_current_news() -> list:
    """Return news fetched in the current pipeline run."""
    return _current_run_data["news"]


# ─── Agent 3: on-chain fetcher (in-memory only) ─────────────────────────────

async def fetch_onchain(symbol: str) -> list:
    """Fetch whale activity for a symbol. Returns in-memory list.
    No DB write.
    """
    # TODO: Replace with Arkham/Nansen/Etherscan API
    events = []  # stub
    _current_run_data["onchain"][symbol] = events
    return events


def get_current_onchain(symbol: str) -> list:
    """Return on-chain events fetched in the current pipeline run."""
    return _current_run_data["onchain"].get(symbol, [])
