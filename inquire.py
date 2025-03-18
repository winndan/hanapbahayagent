import os
import asyncio
import logging
import nest_asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

# ✅ Load environment variables
load_dotenv()
nest_asyncio.apply()

# ✅ Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ✅ Initialize Supabase client
SUPABASE_URL = os.getenv("supa_url")
SUPABASE_KEY = os.getenv("supa_key")

def initialize_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        logging.critical("❌ Supabase credentials are missing! Check environment variables.")
        raise ValueError("Supabase credentials are missing!")
    logging.info("✅ Supabase client initialized successfully.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = initialize_supabase()

# ✅ Define Pydantic models
class InquiryRequest(BaseModel):
    question: str

class RoomData(BaseModel):
    room_number: str
    room_type: str
    description: str
    max_guests: int
    status: str
    price_per_night: float

class ResponseModel(BaseModel):
    answer: str
    rooms: list[RoomData] | None = None

# ✅ Initialize AI Agent for General Inquiries
gem_api = os.getenv("API_KEY")
model = GeminiModel("gemini-2.0-flash", provider=GoogleGLAProvider(api_key=gem_api))

agent = Agent(
    model=model,
    result_type=ResponseModel,
    system_prompt=(
        "You are an AI assistant for a business providing information about available rooms and general inquiries. "
        "Use the available tools to retrieve real data instead of generating responses. "
        "If a user asks about room availability, fetch the data from the database."
    ),
)

@agent.tool
async def get_available_rooms(ctx: RunContext[InquiryRequest]) -> ResponseModel:
    """Fetch available rooms from the database."""
    logging.info(f"🛠️ Fetching available rooms for inquiry: {ctx.deps.question}")

    try:
        response = await asyncio.to_thread(
            lambda: supabase.from_("rooms")
                .select("room_number, room_type, description, max_guests, status, price_per_night")
                .eq("status", "Available")
                .execute()
        )

        if not response.data:
            logging.warning("⚠️ No available rooms found.")
            return ResponseModel(answer="No available rooms at the moment.", rooms=[])

        logging.info(f"✅ Available rooms found: {len(response.data)}")
        rooms = [RoomData(**room) for room in response.data]
        return ResponseModel(answer="Here are the available rooms:", rooms=rooms)

    except Exception as e:
        logging.critical(f"❌ Error retrieving room data: {e}", exc_info=True)
        return ResponseModel(answer="An error occurred while retrieving room availability.", rooms=[])

# ✅ Run the agent
async def main():
    user_question = "show the cheapest rooms?"
    logging.info("\n🚀 Script started!")
    logging.info(f"User inquiry: {user_question}\n")

    try:
        result = await agent.run(
            user_prompt=user_question,
            deps=InquiryRequest(question=user_question)
        )

        logging.info("\n✅ AI Response:")
        if result.data:
            formatted_json = result.data.model_dump_json(indent=2)
            logging.info(f"\n📄 Inquiry Response:\n{formatted_json}")
        else:
            logging.warning("\n⚠️ No data returned from the agent.")

    except Exception as e:
        logging.critical(f"❌ Critical error in main function: {e}", exc_info=True)

if __name__ == "__main__":
    logging.info("⚡ Running async main function...")  
    asyncio.run(main())
    logging.info("✅ Script execution completed!")
