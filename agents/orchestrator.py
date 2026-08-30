# BEFORE
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from agents.tools import read_market_data, read_contextual_data, save_research, search_knowledge_base

def create_orchestrator_agent():
    return create_deep_agent(
        model="openai:gpt-4o",   # ← change this
        ...
    )

# AFTER
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from config.settings import GROQ_API_KEY, GROQ_BASE_URL
from agents.tools import read_market_data, read_contextual_data, save_research, search_knowledge_base

def create_orchestrator_agent():
    groq_model = ChatOpenAI(
        model="openai/gpt-oss-20b",   # or: mixtral-8x7b-32768, gemma2-9b-it, etc.
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        temperature=0.2,
    )
    
    return create_deep_agent(
        model=groq_model,   # ← pass the instance instead of a string
        tools=[read_market_data, read_contextual_data, save_research, search_knowledge_base],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )
