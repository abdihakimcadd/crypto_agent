# Crypto Research Agent System — Deep Agents Implementation (v2)

## Changes from v1

1. **Volume calculation removed from pipeline** → standalone `volume_cron.py`
2. **News fetcher is in-memory only** → no `news_items` table
3. **On-chain fetcher is in-memory only** → no DB write
4. **Pipeline sequence simplified** → news → on-chain → Orchestrator

## Architecture

- **1 Deep Agent** = Orchestrator (Agent 4) — the only LLM caller
- **3 Python functions** = Agents 1-3 — pure data fetchers, no LLM
- **1 standalone script** = `volume_cron.py` — runs on its own cron

## Files

| File | Purpose |
|------|---------|
| `volume_cron.py` | Standalone: fetches Binance candles, calculates volume, upserts to Supabase |
| `config/settings.py` | API keys, thresholds |
| `db/supabase_client.py` | Typed DB helpers |
| `agents/data_fetchers.py` | `get_market_data()` (read-only), `fetch_news()`, `fetch_onchain()` |
| `agents/tools.py` | Deep Agent tools |
| `agents/orchestrator.py` | The ONE Deep Agent |
| `pipeline.py` | 30-min scheduler: news → on-chain → Orchestrator |
| `api.py` | Optional on-demand endpoint |

## Scheduling

Two separate cron jobs:

1. **Volume cron** (every 30 min):
   ```bash
   python volume_cron.py
   ```

2. **Agent pipeline** (every 30 min, offset by 2-3 minutes after volume cron):
   ```bash
   python pipeline.py
   ```

This ensures fresh volume data is in Supabase before the Orchestrator reads it.

## Multi-User Isolation

Per-symbol thread isolation:
```python
thread_id = f"crypto-research-{symbol}"
```

For multi-tenant service:
```python
thread_id = f"user-{user_id}-crypto-{symbol}"
```

## Quick Start

1. `pip install -r requirements.txt`
2. Set `.env`: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY
3. Create Supabase tables (see spec Section 7, minus `news_items`)
4. Seed `symbols` table with your 43 pairs
5. Run `python volume_cron.py` once to populate volume_snapshot
6. Run `python pipeline.py`
