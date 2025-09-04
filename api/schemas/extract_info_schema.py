from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Passenger(BaseModel):
    name: str
    lastName: str
    nationalId: str
    passportNumber: str
    luggageCount: int
    passengerType: str  # "adult" or "infant"
    gender: str


class BookingStateData(BaseModel):
    """Complete booking state data including passenger information"""

    origin_airport: str = ""
    travel_type: str = ""
    travel_date: str = ""
    flight_number: str = ""
    passenger_count: str = ""
    passengers_data: List[Passenger] = []
    additional_info: str = ""


class MessageSender(str, Enum):
    CLIENT = "CLIENT"
    AVATAR = "AVATAR"


class MessageInput(BaseModel):
    id: Optional[str] = None
    text: str
    sender: Optional[MessageSender] = None


class ExtractInfoRequest(BaseModel):
    messages: List[MessageInput]


class ExtractInfoResponse(BaseModel):
    airportName: str
    travelType: str  # "arrival" or "departure"
    travelDate: str
    passengerCount: int
    flightNumber: str
    passengers: List[Passenger]
    additionalInfo: Optional[str] = None


class MessageRequest(BaseModel):
    id: str
    text: str
    sender: MessageSender
