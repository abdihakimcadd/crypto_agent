import json
from langchain_core.tools import tool
from db.supabase_client import write_research_output
from agents.data_fetchers import get_current_news, get_current_onchain


@tool
def read_market_data(symbol: str) -> str:
    """Read volume spike and EMA/MACD indicator data for a symbol from Supabase.

    Args:
        symbol: Binance pair format, e.g. "BTCUSDT"

    Returns:
        JSON string with volume and indicator data.
    """
    from db.supabase_client import supabase

    vol_res = supabase.table("volume_snapshot").select("*").eq("symbol", symbol).execute()
    ind_res = supabase.table("indicator_snapshot").select("*").eq("symbol", symbol).execute()

    vol = vol_res.data[0] if vol_res.data else {}
    ind = ind_res.data[0] if ind_res.data else {}

    return json.dumps({"volume": vol, "indicators": ind})


@tool
def read_contextual_data(symbol: str) -> str:
    """Read news and on-chain events for a symbol (in-memory, current run only).

    Args:
        symbol: Binance pair format, e.g. "BTCUSDT"

    Returns:
        JSON string with news headlines and on-chain events.
    """
    news = get_current_news()
    onchain = get_current_onchain(symbol)

    # Filter news to items that mention this symbol (simple text match)
    symbol_lower = symbol.replace("USDT", "").lower()
    relevant_news = [
        n for n in news
        if symbol_lower in n.get("headline", "").lower()
    ]

    return json.dumps({"news": relevant_news, "onchain": onchain})


@tool
def save_research(symbol: str, summary: str, significance_score: int) -> str:
    """Save the synthesized research output to the database.

    Args:
        symbol: Binance pair format
        summary: 2-4 sentence synthesis
        significance_score: integer 1-10

    Returns:
        Confirmation message.
    """
    from db.supabase_client import supabase

    vol_res = supabase.table("volume_snapshot").select("*").eq("symbol", symbol).execute()
    ind_res = supabase.table("indicator_snapshot").select("*").eq("symbol", symbol).execute()

    vol = vol_res.data[0] if vol_res.data else {}
    ind = ind_res.data[0] if ind_res.data else {}
    onchain = get_current_onchain(symbol)
    news = get_current_news()
    symbol_lower = symbol.replace("USDT", "").lower()
    relevant_news = [n["headline"] for n in news if symbol_lower in n.get("headline", "").lower()]

    write_research_output(
        symbol=symbol,
        summary=summary,
        significance_score=significance_score,
        volume_spike_pct=vol.get("spike_pct"),
        ema_event=ind.get("ema_event"),
        macd_event=ind.get("macd_event"),
        onchain_event=json.dumps(onchain) if onchain else None,
        news_summary="; ".join(relevant_news[:3])
    )
    return f"Research saved for {symbol}"


@tool
def search_knowledge_base(query: str) -> str:
    """Search the internal crypto knowledge base for historical context.

    Args:
        query: Search query, e.g. "Bitcoin halving effects on volume"

    Returns:
        Relevant documents from the knowledge base.
    """
    # TODO: Plug in Milvus/Pinecone vector store
    return "Knowledge base not yet configured."
