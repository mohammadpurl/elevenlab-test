from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Passenger(BaseModel):
    fullName: str
    nationalId: str
    luggageCount: int


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
    travelDate: str
    flightNumber: str
    passengers: List[Passenger]


class MessageRequest(BaseModel):
    id: str
    text: str
    sender: MessageSender
