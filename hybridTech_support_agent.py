import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from tools import TOOLS  # your tools dict

load_dotenv()  

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not PERPLEXITY_API_KEY:
    raise ValueError("Missing PERPLEXITY_API_KEY env variable")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY env variable")

# Perplexity agent (general)
perplexity_model = OpenAIChatModel(
    "sonar-pro",
    provider=OpenAIProvider(
        base_url="https://api.perplexity.ai",
        api_key=PERPLEXITY_API_KEY
    )
)
perplexity_agent = Agent(
    model=perplexity_model,
    name="PerplexityAgent"
)

# OpenAI agent (tool exec)
openai_model = OpenAIChatModel(
    "gpt-4o-mini",
    provider=OpenAIProvider(api_key=OPENAI_API_KEY)
)
openai_agent = Agent(
    model=openai_model,
    tools=[tool["function"] for tool in TOOLS.values()],  # dynamic inclusion of callables
    name="TechSupportAgent"
)
