import os
import asyncio
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from fasthtml.common import *
from monsterui.all import *
from fasthtml.svg import *

# ✅ Load environment variables
load_dotenv()

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
        logging.critical("❌ Supabase credentials are missing!")
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
    price_per_night: float

class BookingRequest(BaseModel):
    booking_id: str

class BookingData(BaseModel):
    guest_name: str
    guest_email: str
    guest_phone: str
    check_in_date: str
    check_out_date: str
    number_of_guests: int
    total_price: float
    status: str
    payment_method: str
    reference_number: str
    created_at: str
    updated_at: str

class ResponseModel(BaseModel):
    answer: str | None = None
    rooms: list[RoomData] | None = None
    booking: BookingData | None = None

# ✅ Initialize AI Agent
gem_api = os.getenv("API_KEY")
model = GeminiModel("gemini-2.0-flash", provider=GoogleGLAProvider(api_key=gem_api))

agent = Agent(
    model=model,
    result_type=ResponseModel,
    system_prompt="You are an AI assistant that helps users inquire about available rooms and fetch booking details. "
                  "Use the available tools to retrieve real data instead of generating responses."
)

@agent.tool
async def get_available_rooms(ctx: RunContext[InquiryRequest]) -> ResponseModel:
    """Fetch available rooms from the database."""
    logging.info(f"🛠️ Fetching available rooms for inquiry: {ctx.deps.question}")

    try:
        response = await asyncio.to_thread(
            lambda: supabase.from_("rooms")
                .select("room_number, room_type, description, max_guests, price_per_night")
                .eq("status", "Available")
                .order("price_per_night", desc=False)
                .execute()
        )

        logging.info(f"📌 Supabase response: {response.data}")

        if not response.data:
            logging.warning("⚠️ No available rooms found.")
            return ResponseModel(answer="No available rooms at the moment.", rooms=[])

        rooms = [RoomData(**room) for room in response.data]
        return ResponseModel(answer="Here are the available rooms:", rooms=rooms)

    except Exception as e:
        logging.critical(f"❌ Error retrieving room data: {e}", exc_info=True)
        return ResponseModel(answer="An error occurred while retrieving room availability.", rooms=[])

@agent.tool
async def get_booking_by_id(ctx: RunContext[BookingRequest]) -> ResponseModel:
    """Fetch a specific booking using the provided booking ID."""
    logging.info(f"🛠️ Fetching booking data for ID: {ctx.deps.booking_id}")

    try:
        response = await asyncio.to_thread(
            lambda: supabase.from_("bookings").select("*").eq("id", ctx.deps.booking_id).maybe_single().execute()
        )

        logging.info(f"📌 Supabase response: {response.data}")

        if not response.data:
            logging.warning(f"⚠️ No booking found for ID {ctx.deps.booking_id}.")
            return ResponseModel(answer="No booking found", booking=None)

        return ResponseModel(answer="Here is your booking:", booking=BookingData(**response.data))

    except Exception as e:
        logging.critical(f"❌ Error retrieving booking: {e}", exc_info=True)
        return ResponseModel(answer="An error occurred while retrieving booking details.", booking=None)

# ✅ FastHTML UI Components
app, rt = fast_app(hdrs=Theme.blue.headers())

def Navbar(active_page):
    return Div(
        DivFullySpaced(
            DivLAligned(
                Img(src='/static/logo-bg.png', height=30, width=30, cls="rounded-full"),
                H3("Bukana Agent", cls="text-lg font-semibold text-gray-900"),
                cls="flex items-center gap-3"
            ),
            Div(
                A("Inquiry", href="/", cls="px-4 py-2 rounded-md transition " + 
                  ("bg-blue-500 text-white shadow-md" if active_page == "inquiry" else "hover:text-blue-500")),
                A("Booking", href="/booking", cls="px-4 py-2 rounded-md transition " + 
                  ("bg-blue-500 text-white shadow-md" if active_page == "booking" else "hover:text-blue-500")),
                cls="flex gap-4"
            ),
            cls="container mx-auto flex justify-between items-center p-4"
        ),
        cls="bg-white shadow-md fixed top-0 w-full z-50"
    )

def ChatbotUI(api_endpoint, placeholder, query_param):
    return Container(
        CardContainer(
            Card(
                CardHeader(H2("Chat with our Agent", cls="text-lg font-semibold text-gray-800")),
                CardBody(
                    Div(id="chat-window", cls="border rounded-lg p-4 h-64 overflow-y-auto bg-gray-50 shadow-inner"),
                    Form(
                        DivLAligned(
                            Input(id="user-input", placeholder=placeholder, 
                                  cls="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"),
                            Button("Ask", cls=ButtonT.primary + " px-4 py-2 rounded-lg hover:bg-blue-600 transition",
                                   type="button", onclick=f"fetchData('{api_endpoint}', '{query_param}')"),
                        ),
                        cls="flex gap-2 mt-3",
                        id="chat-form"
                    ),
                ),
            ),
            cls="w-full max-w-lg mx-auto mt-8 shadow-lg p-4"
        ),
        Script("""
        async function fetchData(api, param) {
            let inputField = document.getElementById('user-input');
            let userInput = inputField.value.trim();
            let chatWindow = document.getElementById('chat-window');

            if (!userInput) {
                chatWindow.innerHTML += "<div class='p-2 bg-red-100 rounded-lg my-1'>❌ Please enter a value.</div>";
                return;
            }

            chatWindow.innerHTML += `<div class='p-2 bg-gray-100 rounded-lg my-1'>🗣️ You: ${userInput}</div>`;
            chatWindow.innerHTML += "<div class='p-2 bg-gray-100 rounded-lg my-1'>🔄 Fetching response...</div>";

            let response = await fetch(`/${api}?${param}=${encodeURIComponent(userInput)}`);
            let data = await response.json();

            chatWindow.innerHTML += `<div class='p-2 bg-blue-100 rounded-lg my-1'>${data.answer || "No data found."}</div>`;
        }
        """)
    )

@rt("/")
def inquiry():
    return Container(
        Navbar("inquiry"),
        ChatbotUI("api/inquire", "Ask about rooms...", "question"),
        cls="mt-24 flex justify-center px-4 md:px-0"
    )

@rt("/booking")
def booking():
    return Container(
        Navbar("booking"),
        ChatbotUI("api/get_booking", "Enter Booking ID...", "booking_id"),
        cls="mt-24 flex justify-center px-4 md:px-0"
    )

serve()
