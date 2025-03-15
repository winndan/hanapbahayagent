import os
import nest_asyncio
from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, Tool, ModelRetry
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import requests

nest_asyncio.apply()  # Enable nested event loops

# Initialize the Gemini Model
gem_api: str = "AIzaSyCs3YLLkXXECqcUwXlsM4WHWm9P7Kt4_l0"  # Replace with your actual API key
model = GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=gem_api))



# --------------------------------------------------------------
# Step 1: Define the response format in a Pydantic model
# --------------------------------------------------------------


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

class EventDetails(BaseModel):
    event: CalendarEvent

class ResponseModel(BaseModel):
    """Structured response with metadata."""

    response: str
    needs_escalation: bool
    follow_up_required: bool
    sentiment: str = Field(description="Customer sentiment analysis")


# --------------------------------------------------------------
# Step 2: Call the model
# --------------------------------------------------------------


agent1 = Agent(
    model=model,
    result_type=CalendarEvent,
    retries=3,
    system_prompt=(
        "Extract the event information."
        
    ) # Add tool via kwarg
)

@agent1.tool_plain()
def get_weather(latitude: float, longitude: float) -> dict:
    """Retrieve weather information for a given location."""
    response = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )
    data = response.json()
    return data.get("current", {})




# --------------------------------------------------------------
# Step 3: Parse the response
# --------------------------------------------------------------

response = agent1.run_sync("Alice and Bob are going to a science fair on Friday.")
print(response.data)
print(response.all_messages())
print(response.usage())

print("*" * 100)

# Access the event details
event = response.data
print(event.name)
print(event.date)
print(event.participants)