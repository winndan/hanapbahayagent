import nest_asyncio
import os
from dataclasses import dataclass
from datetime import date
from uuid import uuid4
from typing import Dict
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, Tool, ModelRetry
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

nest_asyncio.apply()  # Enable nested event loops


class ResponseModel(BaseModel):
    """Structured response with metadata."""

    response: str
    needs_escalation: bool
    follow_up_required: bool
    sentiment: str = Field(description="Customer sentiment analysis")


# Pydantic Models
class Booking(BaseModel):
    id: str
    room_id: str
    room_number: str
    guest_name: str
    guest_email: str
    guest_phone: str
    check_in_date: date
    check_out_date: date
    number_of_guests: int
    total_price: float
    status: str
    payment_method: str


class CustomerDetails(BaseModel):
    user_id: str
    name: str
    email: str
    bookings: list[Booking]


# Simulated database of shipping information
shipping_info_db: Dict[str, str] = {
    "#12345": "Shipped on 2024-12-01",
    "#67890": "Out for delivery",
}


# Tool to get shipping information
def get_shipping_info(ctx: RunContext[CustomerDetails], order_id: str) -> str:
    """Get the shipping status for a given order ID."""
    if not order_id.startswith("#"):
        order_id = f"#{order_id}"  # Auto-correct missing '#'

    return shipping_info_db.get(order_id, "No shipping info found for this order.")



# Initialize the Gemini Model
gem_api: str = "AIzaSyCs3YLLkXXECqcUwXlsM4WHWm9P7Kt4_l0"  # Replace with your actual API key
model = GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=gem_api))


# Agent with reflection and self-correction
agent5 = Agent(
    model=model,
    result_type=ResponseModel,
    deps_type=CustomerDetails,
    retries=3,
    system_prompt=(
        "You are an intelligent customer support agent. "
        "Analyze queries carefully and provide structured responses. "
        "Use tools to look up relevant information. "
        "Always greet the customer and provide a helpful response."
    ),
    tools=[Tool(get_shipping_info, takes_ctx=True)],  # Add tool via kwarg
)


# Example usage
customer = CustomerDetails(
    user_id="1",  # Corrected field name
    name="John Doe",
    email="john.doe@example.com",
    bookings=[  # Added bookings field
        Booking(
            id=str(uuid4()),
            room_id=str(uuid4()),
            room_number="101",
            guest_name="John Doe",
            guest_email="john.doe@example.com",
            guest_phone="123456789",
            check_in_date=date(2025, 3, 15),
            check_out_date=date(2025, 3, 20),
            number_of_guests=2,
            total_price=500.00,
            status="Completed",
            payment_method="eCash",
        )
    ],
)

response = agent5.run_sync(
    user_prompt="What's the status of my last order #12345?"
)
print(f"Agent Response: {response.data.model_dump_json(indent=2)}")

