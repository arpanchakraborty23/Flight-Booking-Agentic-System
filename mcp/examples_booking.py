"""
Example usage of MCP Booking Tool

This demonstrates how to use the booking tool for creating, retrieving, and managing bookings.
"""

from mcp.tools.booking import (
    create_booking,
    get_booking,
    list_bookings,
    cancel_booking,
)


def example_create_booking():
    """Example: Create a flight booking"""
    print("\n📅 Creating a flight booking...\n")

    result = create_booking(
        passenger_name="Rajesh Kumar",
        passenger_email="rajesh.kumar@example.com",
        flight_number="AI123",
        airline="Air India",
        departure_city="DEL",
        arrival_city="BOM",
        departure_date="2026-03-15",
        departure_time="10:30",
        arrival_time="12:30",
        price="₹5,430",
        adults=1,
        children=0,
        infants=0,
    )

    print("✅ Booking Created:")
    for key, value in result.items():
        print(f"   {key}: {value}")

    return result.get("booking_id")


def example_get_booking(booking_id: str):
    """Example: Retrieve booking details"""
    print(f"\n📋 Retrieving booking {booking_id}...\n")

    result = get_booking(booking_id)

    if result["success"]:
        booking = result["booking"]
        print("✅ Booking Details:")
        print(f"   Booking ID: {booking['booking_id']}")
        print(f"   Passenger: {booking['passenger']['name']}")
        print(f"   Flight: {booking['flight']['airline']} {booking['flight']['number']}")
        print(f"   Route: {booking['flight']['departure_city']} → {booking['flight']['arrival_city']}")
        print(f"   Date: {booking['flight']['departure_date']}")
        print(f"   Time: {booking['flight']['departure_time']} - {booking['flight']['arrival_time']}")
        print(f"   Price: {booking['pricing']['total_price']}")
        print(f"   Status: {booking['status']}")
    else:
        print(f"❌ {result['message']}")


def example_list_bookings():
    """Example: List all bookings"""
    print("\n📊 Listing all bookings...\n")

    result = list_bookings(limit=5)

    if result["success"]:
        print(f"✅ Found {result['count']} bookings:")
        for booking in result["bookings"]:
            print(f"   - {booking['booking_id']}: {booking['passenger']['name']} ({booking['flight']['airline']} {booking['flight']['number']})")
    else:
        print("❌ No bookings found")


def example_list_bookings_by_email(email: str):
    """Example: List bookings for a specific email"""
    print(f"\n📧 Listing bookings for {email}...\n")

    result = list_bookings(email=email)

    if result["success"]:
        print(f"✅ Found {result['count']} bookings for {email}:")
        for booking in result["bookings"]:
            print(f"   - {booking['booking_id']}: {booking['flight']['airline']} {booking['flight']['number']} on {booking['flight']['departure_date']}")
    else:
        print("❌ No bookings found for this email")


def example_cancel_booking(booking_id: str):
    """Example: Cancel a booking"""
    print(f"\n❌ Cancelling booking {booking_id}...\n")

    result = cancel_booking(
        booking_id=booking_id,
        reason="Changed travel plans",
    )

    if result["success"]:
        print(f"✅ Booking cancelled:")
        print(f"   Booking ID: {result['booking_id']}")
        print(f"   Status: {result['status']}")
        print(f"   {result['message']}")
    else:
        print(f"❌ {result['message']}")


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Booking Tool - Usage Examples")
    print("=" * 60)

    # Example 1: Create a booking
    booking_id = example_create_booking()

    # Example 2: Retrieve the booking
    if booking_id:
        example_get_booking(booking_id)

    # Example 3: Create another booking for the same email
    result = create_booking(
        passenger_name="Priya Singh",
        passenger_email="rajesh.kumar@example.com",  # Same email as first booking
        flight_number="AI456",
        airline="Air India",
        departure_city="BOM",
        arrival_city="BLR",
        departure_date="2026-04-20",
        departure_time="14:00",
        arrival_time="16:00",
        price="₹3,200",
        adults=1,
    )
    second_booking_id = result.get("booking_id")

    # Example 4: List all bookings
    example_list_bookings()

    # Example 5: List bookings for a specific email
    example_list_bookings_by_email("rajesh.kumar@example.com")

    # Example 6: Cancel a booking
    if second_booking_id:
        example_cancel_booking(second_booking_id)

    # Example 7: Verify cancellation
    if second_booking_id:
        example_get_booking(second_booking_id)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
