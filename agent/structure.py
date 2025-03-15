from typing import Dict, List, Optional
import nest_asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
gem_api : str = os.getenv("API_KEY")

model = GeminiModel(
    'gemini-2.0-flash', provider=GoogleGLAProvider(api_key=gem_api)
)
basic_agent = Agent(model=model,
              system_prompt = "You are helpful travel assistant")

response = basic_agent.run_sync("How to travel from china to US")
print(response.data)
print(response.all_messages())
print(response.usage())

response2 = basic_agent.run_sync(
    user_prompt="What was my previous question?",
    message_history=response.new_messages(),
)

print(response2.data)

print("-" * 100)



class ResponseModel(BaseModel):
    """Structured response with metadata."""

    response: str
    needs_escalation: bool
    follow_up_required: bool
    sentiment: str = Field(description="Customer sentiment analysis")


agent2 = Agent(
    model=model,
    result_type=ResponseModel,
    system_prompt=(
        "You are an intelligent customer support agent. "
        "Analyze queries carefully and provide structured responses."
    ),
)

response = agent2.run_sync("How can I track my order #12345?")
print(response.data.model_dump_json(indent=2))
