
import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from tools import TOOLS  # all tools dynamically registered

from env_config import *


def create_agents():
    """First Checking for key availability, then Creating and return Perplexity and OpenAI agents."""

    if not PERPLEXITY_API_KEY:
        logger.error("❌ PERPLEXITY_API_KEY missing. Please set it in .env file.")
        raise ValueError("Please set your PERPLEXITY_API_KEY environment config")
    if not OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY missing. Please set it in .env file.")
        raise ValueError("Please set your OPENAI_API_KEY environment config")

    # Perplexity Agent - general chat

    perplexity_model = OpenAIChatModel(
        "sonar-pro",
        provider=OpenAIProvider(
            base_url="https://api.perplexity.ai",
            api_key=PERPLEXITY_API_KEY
        )
    )
    perplexity_agent = Agent(model=perplexity_model, name="PerplexityAgent")
    logger.info("✅ Perplexity agent initialized successfully.")


    # OpenAI Agent - tool execution
    openai_model = OpenAIChatModel(
        "gpt-4o-mini",
        provider=OpenAIProvider(api_key=OPENAI_API_KEY)
    )
    openai_agent = Agent(
        model=openai_model,
        tools=[tool["function"] for tool in TOOLS.values()],  # dynamic registration
        name="TechSupportAgent"
    )
    logger.info("✅ OpenAI TechSupportAgent initialized with registered tools.")
    return perplexity_agent, openai_agent
