# import os
# import google.generativeai as genai
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Configure Gemini API
# genai.configure(api_key=os.getenv("API_KEY"))

# # OpenAI-style messages with a "system" prompt workaround
# messages = [
#     {"role": "system", "content": "You're a helpful assistant."},
#     {"role": "user", "content": "Write a limerick about the Python programming language."}
# ]

# # Convert to Gemini format (embedding system prompt as a user message)
# gemini_messages = [
#     {"role": "user", "parts": [{"text": "[SYSTEM] " + msg["content"]}]} if msg["role"] == "system" 
#     else {"role": "user", "parts": [{"text": msg["content"]}]}
#     for msg in messages
# ]

# # Send request to Gemini
# model = genai.GenerativeModel("gemini-2.0-flash")
# response = model.generate_content(gemini_messages)

# # Print AI response
# print(response.text)

from typing import Dict, List, Optional
import nest_asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import os


nest_asyncio.apply()  # Enable nested event loops

gem_api : str = "AIzaSyCs3YLLkXXECqcUwXlsM4WHWm9P7Kt4_l0"

model = GeminiModel(
    'gemini-2.0-flash', provider=GoogleGLAProvider(api_key=gem_api)
)
basic_agent = Agent(model=model,
              system_prompt = "You are helpful travel assistant for my booking app")

response = basic_agent.run_sync("I want my booking status for this id f80ed3fa-2c21-44f5-a7b2-fc3e19164df2")
print(response.data)
print(response.all_messages())
print(response.usage())

response2 = basic_agent.run_sync(
    user_prompt="What was my previous question?",
    message_history=response.new_messages(),
)

print(response2.data)

print("-" * 100)


