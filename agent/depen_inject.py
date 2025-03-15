import os
from dataclasses import dataclass
from datetime import date
from uuid import uuid4
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

# Load API Key from environment variable
gem_api: str = "AIzaSyCs3YLLkXXECqcUwXlsM4WHWm9P7Kt4_l0"  # Ensure this is set correctly in your environment

# Initialize the Gemini Model
model = GeminiModel(
    'gemini-2.0-flash', provider=GoogleGLAProvider(api_key=gem_api)
)

# Create AI Agent
basic_agent = Agent(
    model=model,
    system_prompt=(
        "You are a helpful travel assistant that provides booking details based on user input. "
        "The user's booking details are provided below. Use them to answer their questions. "
        "If the user asks about a booking but does not provide enough details, ask them for a "
        "booking reference number, dates, or destination to help locate their booking information."
    ),
)

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


class UserDetails(BaseModel):
    user_id: str
    name: str
    email: str
    bookings: list[Booking]


# Dependency Injection using Dataclass
@dataclass
class CustomerDeps:
    customer: UserDetails

    def system_prompt_factory(self) -> str:
        customer_details = ", ".join(
            f"{key}: {value}"
            for key, value in self.customer.model_dump().items()
            if key != "bookings"
        )
        booking_details = "\n".join(
            f"Booking {i + 1}: Room {booking.room_number}, Check-in: {booking.check_in_date}, "
            f"Check-out: {booking.check_out_date}, Guests: {booking.number_of_guests}, "
            f"Total Price: ${booking.total_price}, Status: {booking.status}"
            for i, booking in enumerate(self.customer.bookings)
        )
        return (
            f"Customer details: {customer_details}\n"
            f"Bookings:\n{booking_details}"
        )


# Define System Prompt Handler
@basic_agent.system_prompt
async def add_customer_name(ctx: RunContext[CustomerDeps]) -> str:
    return ctx.deps.system_prompt_factory()


# Example User Data
customer = UserDetails(
    user_id="1",
    name="John Doe",
    email="john.doe@example.com",
    bookings=[
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


# Running the AI Agent
async def main():
    deps = CustomerDeps(customer=customer)
    response = await basic_agent.run("What did I book?", deps=deps)

    # Print Customer Details and Response
    print(
        "Customer Details:\n"
        f"Name: {customer.name}\n"
        f"Email: {customer.email}\n\n"
        "Response:\n"
        f"{response.data}"
    )


# Run the script
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())