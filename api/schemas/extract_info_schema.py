from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Passenger(BaseModel):
    name: str
    lastName: str
    nationalId: str
    flightNumber: str
    passportNumber: str
    luggageCount: int
    passengerType: str  # "adult" or "infant"
    gender: str


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
    passengers: List[Passenger]
    additionalInfo: Optional[str] = None


class MessageRequest(BaseModel):
    id: str
    text: str
    sender: MessageSender
