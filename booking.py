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
    level=logging.INFO,  # Change to DEBUG for detailed logs
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
class BookingRequest(BaseModel):
    booking_id: str

class BookingData(BaseModel):
    id: str
    guest_name: str | None = None
    guest_email: str | None = None
    guest_phone: str | None = None
    check_in_date: str | None = None
    check_out_date: str | None = None
    number_of_guests: int | None = None
    total_price: float | None = None
    status: str | None = None
    payment_method: str | None = None
    reference_number: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

class ResponseModel(BaseModel):
    booking: BookingData | None = None
    message: str

# ✅ Initialize Gemini Model
gem_api = os.getenv("API_KEY")
model = GeminiModel("gemini-2.0-flash", provider=GoogleGLAProvider(api_key=gem_api))

# ✅ Create AI Agent
agent = Agent(
    model=model,
    result_type=ResponseModel,
    system_prompt=(
        "You are an AI agent that fetches booking details from Supabase. "
        "Always use the provided tools to fetch real data instead of generating responses."
    ),
)

@agent.tool
async def get_booking_by_id(ctx: RunContext[BookingRequest]) -> ResponseModel:
    """Fetch a specific booking using the provided booking ID."""
    logging.info("🛠️ get_booking_by_id tool called!")

    try:
        booking_id = ctx.deps.booking_id
        logging.debug(f"🔍 Fetching booking with ID: {booking_id}")

        # ✅ Run Supabase query in a separate thread
        response = await asyncio.to_thread(
            lambda: supabase.from_("bookings").select("*").eq("id", booking_id).maybe_single().execute()
        )

        logging.debug(f"📜 Raw Supabase Response: {response}")

        if not response.data:
            logging.warning("⚠️ No booking found in database.")
            return ResponseModel(booking=None, message="No booking found")

        booking_data = response.data
        logging.info(f"✅ Booking Found: {booking_data}")

        # ✅ Parse booking data safely
        try:
            parsed_data = BookingData(**{key: booking_data.get(key) for key in BookingData.model_fields})
            logging.debug(f"✅ Parsed Booking Data: {parsed_data}")
            return ResponseModel(booking=parsed_data, message="Booking retrieved successfully")
        except Exception as parse_error:
            logging.error(f"❌ Error parsing booking data: {parse_error}")
            return ResponseModel(booking=None, message="Data format error")

    except Exception as e:
        logging.critical(f"❌ Critical error retrieving booking: {e}", exc_info=True)
        return ResponseModel(booking=None, message=f"Unexpected error: {str(e)}")

# ✅ Run the agent
async def main():
    booking_id = "0b4d20c8-1a1a-45eb-b7f8-005a97981cbe"
    logging.info("\n🚀 Script started!")
    logging.info(f"Fetching booking with ID: {booking_id}\n")

    try:
        result = await agent.run(
            user_prompt=f"give all the details for llanesdanmarc@gmail.com? {booking_id} using the tool.",
            deps=BookingRequest(booking_id=booking_id)
        )

        logging.info("\n✅ Agent Response:")
        if result.data:
            formatted_json = result.data.model_dump_json(indent=2)
            logging.info(f"\n📄 Booking Data:\n{formatted_json}")
        else:
            logging.warning("\n⚠️ No data returned from the agent.")

        # ✅ Print usage statistics safely
        usage_info = result.usage()
        logging.info(f"📊 Usage Info: {usage_info}")  
        if hasattr(usage_info, "tokens_used"):
            logging.info(f"📥 Tokens Used: {usage_info.tokens_used}")

    except Exception as e:
        logging.critical(f"❌ Critical error in main function: {e}", exc_info=True)

if __name__ == "__main__":
    logging.info("⚡ Running async main function...")  
    asyncio.run(main())
    logging.info("✅ Script execution completed!")