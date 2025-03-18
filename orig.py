from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional, Union
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from supabase import create_client, AsyncClient
import asyncio
import json
from dataclasses import dataclass

# --- Pydantic Models for Conversation History ---

class ConversationMessage(BaseModel):
    role: str = Field(..., description="The role of the message, e.g., 'system', 'user', or 'assistant'.")
    content: str = Field(..., description="The text content of the message.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the message.")

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class Conversation(BaseModel):
    query: str
    response: str
    messages: Optional[List[ConversationMessage]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

# --- Dependency Model ---
@dataclass
class BookingDeps:
    date: Optional[str] = None
    email: Optional[str] = None

# --- Initialize Supabase client ---
try:
    client: AsyncClient = create_client(
        "https://yfswjewyxnrrifsvvewq.supabase.co",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlmc3dqZXd5eG5ycmlmc3Z2ZXdxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk5MzYzMzAsImV4cCI6MjA1NTUxMjMzMH0.WRxkf39I2OeyuZAYpD1090pgV0QeNC_viEYtGBIJtis"
    )
    print("Supabase connected successfully!")
except Exception as e:
    print(f"Supabase connection failed: {str(e)}")
    exit(1)

# --- Configure Gemini ---
try:
    gem_api = "AIzaSyCs3YLLkXXECqcUwXlsM4WHWm9P7Kt4_l0"
    model = GeminiModel(
        'gemini-2.0-flash',
        provider=GoogleGLAProvider(api_key=gem_api)
    )
    print("Gemini configured successfully!")
except Exception as e:
    print(f"Gemini configuration failed: {str(e)}")
    exit(1)

# --- Create the Agent ---
agent = Agent(
    model=model,
    system_prompt="You are a booking assistant. Retrieve bookings based on date or email.",
    deps_type=BookingDeps
)

@agent.tool
async def retrieve_from_supabase(ctx: RunContext[BookingDeps]) -> Union[list, str]:
    """
    Retrieve room bookings based on check-in date or email.
    Returns an error message if the table is missing.
    """
    try:
        filters = []
        if ctx.deps.date:
            filters.append(f"check_in_date.eq.{ctx.deps.date}")
        if ctx.deps.email:
            filters.append(f"email.eq.{ctx.deps.email}")

        if not filters:
            return "Please provide a date or an email to search for bookings."

        query = client.from_("bookings").select("*")
        for f in filters:
            query = query.filter(f)

        response = await query.execute()

        if response.data:
            print(f"Retrieved {len(response.data)} records")
            return response.data
        else:
            return "No bookings found."

    except Exception as e:
        error = str(e)
        print(f"Database error: {error}")
        return "Error retrieving bookings."

@agent.tool
async def generate_response(ctx: RunContext[BookingDeps]) -> str:
    """Generates a response based on retrieved booking data."""
    try:
        data = await retrieve_from_supabase(ctx)
        if isinstance(data, str):
            return data
        return f"Found {len(data)} records related to your query."
    except Exception as e:
        print(f"Processing error: {str(e)}")
        return "Unable to process your request."

# --- Main Function ---
async def main():
    try:
        deps = BookingDeps(date="2025-03-25", email=None)  # Example usage

        print("Starting query...")
        result = await agent.run('What is my latest room booking?', deps=deps)

        print(f"Agent response: {result.data}")

        if result.data:
            raw_messages = result.all_messages() if hasattr(result, "all_messages") else []
            messages = [
                ConversationMessage(
                    role=getattr(msg, "kind", "unknown"),
                    content=getattr(msg, "content", str(msg)),
                    timestamp=getattr(msg, "timestamp", datetime.now(timezone.utc))
                )
                for msg in raw_messages
            ]

            conversation = Conversation(
                query="What is my latest room booking?",
                response=str(result.data),
                messages=messages
            )

            conversation_data = json.loads(conversation.model_dump_json())
            print(f"Inserting conversation: {conversation_data}")

            try:
                insert_response = await client.from_("conversations").insert(conversation_data).execute()
                print("Data stored successfully!")
                print("Insert response:", insert_response)
            except Exception as e:
                print(f"Failed to insert data into Supabase: {str(e)}")

        return result.data

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())
