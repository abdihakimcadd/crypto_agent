"""
volume_cron.py

Runs every 30 minutes (AFTER volume_backfill.py has been run once).
For each symbol:
  1. Fetch only the newest closed 30-min candle from Binance (1 fast call)
  2. Append it to volume_history
  3. Delete volume_history rows older than 30 days for that symbol
  4. Calculate average_volume from what's stored in volume_history
  5. Upsert the result into volume_snapshot

This is deliberately lightweight compared to the backfill script — it
never refetches the full 30-day window, it only adds one new candle and
reads the average from the database.

Requires a .env file with:
  SUPABASE_URL=...
  SUPABASE_KEY=...

Requires packages:
  pip install supabase requests python-dotenv --break-system-packages
"""

import os
import time
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
INTERVAL = "30m"
RETENTION_DAYS = 30
SPIKE_SIGNIFICANCE_THRESHOLD = 100.0  # %


def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_symbols(supabase: Client) -> list[str]:
    response = supabase.table("symbols").select("symbol_name").execute()
    return [row["symbol_name"] for row in response.data if row.get("symbol_name")]


def fetch_latest_closed_candle(symbol: str) -> dict:
    """
    Fetch the last 2 candles and use the second-most-recent one — this
    guarantees we get a fully CLOSED candle, not one still forming.
    """
    params = {"symbol": symbol, "interval": INTERVAL, "limit": 2}
    resp = requests.get(BINANCE_KLINES_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if len(data) < 2:
        raise ValueError(f"Not enough candle data returned for {symbol}")

    closed_candle = data[-2]  # guaranteed closed
    candle_time = datetime.fromtimestamp(closed_candle[0] / 1000, tz=timezone.utc)
    volume = float(closed_candle[5])

    return {"candle_time": candle_time, "volume": volume}


def append_to_history(supabase: Client, symbol: str, candle: dict) -> None:
    """Insert the new candle. Unique(symbol, candle_time) makes this safe to rerun."""
    supabase.table("volume_history").upsert({
        "symbol": symbol,
        "candle_time": candle["candle_time"].isoformat(),
        "volume": candle["volume"],
    }, on_conflict="symbol,candle_time").execute()


def prune_old_history(supabase: Client, symbol: str) -> None:
    """Delete rows older than the retention window to keep the table rolling."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    supabase.table("volume_history") \
        .delete() \
        .eq("symbol", symbol) \
        .lt("candle_time", cutoff) \
        .execute()


def calculate_average_from_history(supabase: Client, symbol: str, current_volume: float) -> dict:
    """
    Pull all stored volume rows for this symbol and calculate the average,
    excluding the current/newest candle from the average itself.
    """
    response = supabase.table("volume_history") \
        .select("volume, candle_time") \
        .eq("symbol", symbol) \
        .order("candle_time", desc=True) \
        .execute()

    rows = response.data
    if len(rows) < 2:
        raise ValueError(f"Not enough history stored for {symbol} to calculate average")

    # Exclude the most recent row (the one we just added) from the average
    historical_volumes = [float(r["volume"]) for r in rows[1:]]
    average_volume = sum(historical_volumes) / len(historical_volumes)

    if average_volume == 0:
        spike_pct = 0.0
    else:
        spike_pct = ((current_volume - average_volume) / average_volume) * 100

    return {
        "current_volume": current_volume,
        "average_volume": average_volume,
        "spike_pct": spike_pct,
        "is_significant": abs(spike_pct) >= SPIKE_SIGNIFICANCE_THRESHOLD,
    }


def store_snapshot(supabase: Client, symbol: str, stats: dict) -> None:
    supabase.table("volume_snapshot").upsert({
        "symbol": symbol,
        "current_volume": stats["current_volume"],
        "average_volume": stats["average_volume"],
        "spike_pct": stats["spike_pct"],
        "is_significant": stats["is_significant"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="symbol").execute()


def process_symbol(supabase: Client, symbol: str) -> None:
    candle = fetch_latest_closed_candle(symbol)
    append_to_history(supabase, symbol, candle)
    prune_old_history(supabase, symbol)
    stats = calculate_average_from_history(supabase, symbol, candle["volume"])
    store_snapshot(supabase, symbol, stats)

    flag = " *** SIGNIFICANT SPIKE ***" if stats["is_significant"] else ""
    print(
        f"[{symbol}] current={stats['current_volume']:.2f} "
        f"avg={stats['average_volume']:.2f} "
        f"spike={stats['spike_pct']:.1f}%{flag}"
    )


def main():
    supabase = get_supabase_client()
    symbols = get_symbols(supabase)

    if not symbols:
        print("No symbols found in `symbols` table.")
        return

    print(f"Running volume cron for {len(symbols)} symbols...\n")

    for symbol in symbols:
        try:
            process_symbol(supabase, symbol)
        except Exception as e:
            print(f"[{symbol}] ERROR — {e}")
        time.sleep(0.1)

    print("\nDone.")


if __name__ == "__main__":
    main()
