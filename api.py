from fastapi import FastAPI
from agents.orchestrator import create_orchestrator_agent
from agents.data_fetchers import fetch_news, fetch_onchain
from langchain_core.messages import HumanMessage
import asyncio

app = FastAPI()


@app.post("/research/{symbol}")
async def research_symbol(symbol: str, user_id: str = "default"):
    """On-demand research for a specific symbol, isolated per user."""
    # Fetch fresh contextual data in-memory
    await fetch_news()
    await fetch_onchain(symbol)

    orchestrator = create_orchestrator_agent()

    result = await orchestrator.ainvoke(
        {"messages": [HumanMessage(content=f"Analyze {symbol}")]},
        config={"configurable": {"thread_id": f"user-{user_id}-crypto-{symbol}"}}
    )

    return {
        "symbol": symbol,
        "user_id": user_id,
        "research": result["messages"][-1].content
    }
