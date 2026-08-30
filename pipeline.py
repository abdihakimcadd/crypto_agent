import asyncio
from datetime import datetime, timedelta, timezone
from db.supabase_client import get_symbols, supabase
from agents.data_fetchers import fetch_news, fetch_onchain
from agents.orchestrator import create_orchestrator_agent
from langchain_core.messages import HumanMessage


def is_volume_data_fresh(symbol: str, max_age_minutes: int = 10) -> bool:
    """Check if volume_snapshot for this symbol was updated recently."""
    res = supabase.table("volume_snapshot") \
        .select("updated_at") \
        .eq("symbol", symbol) \
        .execute()

    if not res.data:
        return False

    updated_at = datetime.fromisoformat(res.data[0]["updated_at"].replace("Z", "+00:00"))
    age = datetime.now(timezone.utc) - updated_at

    return age <= timedelta(minutes=max_age_minutes)


async def should_process(symbol: str) -> bool:
    """Check if symbol has any significant events this cycle."""
    from db.supabase_client import get_volume_snapshot, get_indicator_snapshot

    vol = get_volume_snapshot(symbol)
    ind = get_indicator_snapshot(symbol)

    has_volume = vol.get("is_significant", False)
    has_ema = ind.get("ema_event") is not None
    has_macd = ind.get("macd_event") is not None

    return has_volume or has_ema or has_macd


async def run_pipeline():
    """Main pipeline: fetch in-memory data, then Orchestrator (Deep Agent)."""
    print(f"[{datetime.utcnow()}] Starting pipeline...")
    symbols = get_symbols()
    print(f"Processing {len(symbols)} symbols...")

    # Step 1: Fetch news (in-memory only, no DB write)
    print("Fetching news...")
    await fetch_news()

    # Step 2: Fetch on-chain data (in-memory only, no DB write)
    print("Fetching on-chain data...")
    await asyncio.gather(*[fetch_onchain(s) for s in symbols])

    # Step 3: Orchestrator (Deep Agent)
    print("Running Orchestrator Agent...")
    orchestrator = create_orchestrator_agent()

    processed = 0
    skipped = 0
    stale = 0

    for symbol in symbols:
        # Freshness guard: skip if volume data is stale
        if not is_volume_data_fresh(symbol):
            print(f"  {symbol}: volume data stale, skipping")
            stale += 1
            continue

        if not await should_process(symbol):
            skipped += 1
            continue

        # Per-symbol thread isolation
        thread_id = f"crypto-research-{symbol}"

        result = await orchestrator.ainvoke(
            {"messages": [HumanMessage(content=f"Analyze {symbol}")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        print(f"  {symbol}: {result['messages'][-1].content[:100]}...")
        processed += 1

    print(f"Done. Processed: {processed}, Skipped (no signal): {skipped}, Stale data: {stale}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
