from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_volume_snapshot(symbol: str) -> dict:
    """Read latest volume data for a symbol."""
    res = supabase.table("volume_snapshot").select("*").eq("symbol", symbol).execute()
    return res.data[0] if res.data else {}


def get_indicator_snapshot(symbol: str) -> dict:
    """Read latest EMA/MACD events for a symbol."""
    res = supabase.table("indicator_snapshot").select("*").eq("symbol", symbol).execute()
    return res.data[0] if res.data else {}


def get_symbols() -> list:
    """Read all watchlist symbols."""
    res = supabase.table("symbols").select("symbol_name").execute()
    return [r["symbol_name"] for r in res.data]


def write_research_output(symbol: str, summary: str, significance_score: int,
                          volume_spike_pct: float = None, ema_event: str = None,
                          macd_event: str = None, onchain_event: str = None,
                          news_summary: str = None) -> dict:
    """Upsert research row."""
    data = {
        "symbol": symbol,
        "summary": summary,
        "significance_score": significance_score,
        "volume_spike_pct": volume_spike_pct,
        "ema_event": ema_event,
        "macd_event": macd_event,
        "onchain_event": onchain_event,
        "news_summary": news_summary,
    }
    res = supabase.table("research_output").upsert(data).execute()
    return res.data
