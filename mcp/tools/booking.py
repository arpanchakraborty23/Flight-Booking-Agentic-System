from typing import Optional, Dict, Any
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# MCP-internal imports (no backend dependencies)
from utils.logger import setup_logger
from utils.exception import MCPException

load_dotenv()

logger = setup_logger(name="mcp_booking_agent")

# MongoDB connection (optional - will work without it)
try:
    from pymongo import MongoClient
    HAS_MONGODB = True
except ImportError:
    HAS_MONGODB = False
    logger.warning("pymongo not installed - bookings will be stored in memory")

# In-memory fallback storage
IN_MEMORY_BOOKINGS: Dict[str, Dict[str, Any]] = {}


class BookingService:
    """
    Service to handle flight bookings with MongoDB storage.
    Falls back to in-memory storage if MongoDB is unavailable.
    """

    def __init__(self):
        self.db = None
        self.bookings_collection = None
        self._init_mongodb()

    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        if not HAS_MONGODB:
            logger.info("In-memory storage mode (MongoDB not available)")
            return

        try:
            mongodb_uri = os.getenv(
                "MONGODB_URI",
                "mongodb://localhost:27017"
            )
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            client.admin.command('ping')
            
            self.db = client.get_database("flight_bookings")
            self.bookings_collection = self.db.get_collection("bookings")
            
            # Create index on booking_id for fast lookup
            self.bookings_collection.create_index("booking_id", unique=True)
            
            logger.info("✅ Connected to MongoDB successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB: {e} - using in-memory storage")
            self.db = None
            self.bookings_collection = None

    def create_booking(
        self,
        passenger_name: str,
        passenger_email: str,
        flight_number: str,
        airline: str,
        departure_city: str,
        arrival_city: str,
        departure_date: str,
        departure_time: str,
        arrival_time: str,
        price: str,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
    ) -> Dict[str, Any]:
        """
        Create and store a flight booking.

        Args:
            passenger_name: Full name of passenger
            passenger_email: Email address
            flight_number: Flight number (e.g., "AI123")
            airline: Airline name
            departure_city: Departure city code (e.g., "DEL")
            arrival_city: Arrival city code (e.g., "BOM")
            departure_date: Date in YYYY-MM-DD format
            departure_time: Time in HH:MM format
            arrival_time: Time in HH:MM format
            price: Price in INR (e.g., "₹5,430" or "5430")
            adults: Number of adults
            children: Number of children
            infants: Number of infants

        Returns:
            Dict with booking confirmation details including booking_id
        """
        try:
            # Generate unique booking ID
            booking_id = f"BK{uuid.uuid4().hex[:10].upper()}"

            # Create booking document
            booking_doc = {
                "booking_id": booking_id,
                "passenger": {
                    "name": passenger_name,
                    "email": passenger_email,
                },
                "flight": {
                    "number": flight_number,
                    "airline": airline,
                    "departure_city": departure_city,
                    "arrival_city": arrival_city,
                    "departure_date": departure_date,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                },
                "passengers": {
                    "adults": adults,
                    "children": children,
                    "infants": infants,
                },
                "pricing": {
                    "total_price": price,
                    "currency": "INR"
                },
                "status": "CONFIRMED",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Store in MongoDB or in-memory
            if self.bookings_collection is not None:
                result = self.bookings_collection.insert_one(booking_doc)
                logger.info(f"✅ Booking {booking_id} stored in MongoDB")
            else:
                IN_MEMORY_BOOKINGS[booking_id] = booking_doc
                logger.info(f"✅ Booking {booking_id} stored in memory")

            return {
                "success": True,
                "booking_id": booking_id,
                "passenger_name": passenger_name,
                "flight_number": flight_number,
                "departure_date": departure_date,
                "status": "CONFIRMED",
                "message": f"Your booking is confirmed! Booking ID: {booking_id}. "
                          f"Confirmation details have been sent to {passenger_email}.",
            }

        except Exception as e:
            logger.error(f"Failed to create booking: {e}")
            raise MCPException(e, None)

    def get_booking(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a booking by ID.

        Args:
            booking_id: The booking ID to retrieve

        Returns:
            Booking details or None if not found
        """
        try:
            if self.bookings_collection is not None:
                booking = self.bookings_collection.find_one({"booking_id": booking_id})
            else:
                booking = IN_MEMORY_BOOKINGS.get(booking_id)

            if booking:
                # Remove MongoDB _id field from response
                if "_id" in booking:
                    del booking["_id"]
                return booking
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve booking {booking_id}: {e}")
            raise MCPException(e, None)

    def list_bookings(self, email: Optional[str] = None, limit: int = 10) -> list:
        """
        List bookings, optionally filtered by email.

        Args:
            email: Filter by passenger email (optional)
            limit: Maximum number of results

        Returns:
            List of bookings
        """
        try:
            query = {}
            if email:
                query["passenger.email"] = email

            if self.bookings_collection is not None:
                bookings = list(
                    self.bookings_collection.find(query).limit(limit)
                )
            else:
                bookings = [
                    b for b in IN_MEMORY_BOOKINGS.values()
                    if not email or b["passenger"]["email"] == email
                ][:limit]

            # Remove MongoDB _id field from responses
            for booking in bookings:
                if "_id" in booking:
                    del booking["_id"]

            return bookings

        except Exception as e:
            logger.error(f"Failed to list bookings: {e}")
            raise MCPException(e, None)

    def cancel_booking(self, booking_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Cancel a booking.

        Args:
            booking_id: The booking to cancel
            reason: Cancellation reason

        Returns:
            Cancellation confirmation
        """
        try:
            update_doc = {
                "status": "CANCELLED",
                "cancellation_reason": reason,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if self.bookings_collection is not None:
                result = self.bookings_collection.update_one(
                    {"booking_id": booking_id},
                    {"$set": update_doc}
                )
                if result.matched_count == 0:
                    return {
                        "success": False,
                        "message": f"Booking {booking_id} not found",
                    }
            else:
                if booking_id not in IN_MEMORY_BOOKINGS:
                    return {
                        "success": False,
                        "message": f"Booking {booking_id} not found",
                    }
                IN_MEMORY_BOOKINGS[booking_id].update(update_doc)

            logger.info(f"✅ Booking {booking_id} cancelled")
            return {
                "success": True,
                "booking_id": booking_id,
                "status": "CANCELLED",
                "message": f"Booking {booking_id} has been cancelled.",
            }

        except Exception as e:
            logger.error(f"Failed to cancel booking {booking_id}: {e}")
            raise MCPException(e, None)


# Initialize booking service
booking_service = BookingService()
