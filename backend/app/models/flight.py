# backend/app/models/flight.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Flight:
    """航班信息模型"""
    flightNumber: str
    departureTime: str
    arrivalTime: str
    duration: str
    stops: int
    stopoverCities: List[str] = field(default_factory=list)
    airline: str = ""
    airlineCode: str = ""
    price: float = 0.0
    currency: str = "CNY"
    seatsRemaining: int = 0
    cabin: str = "economy"

    def to_dict(self) -> dict:
        return {
            "flightNumber": self.flightNumber,
            "departureTime": self.departureTime,
            "arrivalTime": self.arrivalTime,
            "duration": self.duration,
            "stops": self.stops,
            "stopoverCities": self.stopoverCities,
            "airline": self.airline,
            "airlineCode": self.airlineCode,
            "price": self.price,
            "currency": self.currency,
            "seatsRemaining": self.seatsRemaining,
            "cabin": self.cabin
        }

@dataclass
class FlightSegment:
    """航段信息（用于拼接）"""
    from_airport: str
    to_airport: str
    airline: str
    airlineCode: str
    departureTime: str
    arrivalTime: str
    price: float
    duration: str

    def to_dict(self) -> dict:
        return {
            "from": self.from_airport,
            "to": self.to_airport,
            "airline": self.airline,
            "airlineCode": self.airlineCode,
            "departureTime": self.departureTime,
            "arrivalTime": self.arrivalTime,
            "price": self.price,
            "duration": self.duration
        }

@dataclass
class SplicedRoute:
    """拼接路线"""
    totalPrice: float
    totalDuration: str
    stops: int
    segments: List[FlightSegment]
    currency: str = "CNY"

    def to_dict(self) -> dict:
        return {
            "totalPrice": self.totalPrice,
            "totalDuration": self.totalDuration,
            "stops": self.stops,
            "segments": [s.to_dict() for s in self.segments],
            "currency": self.currency
        }

@dataclass
class DestinationInfo:
    """目的地信息"""
    destination: str
    city: str
    country: str
    lowestPrice: float
    currency: str = "CNY"
    flightDate: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "destination": self.destination,
            "city": self.city,
            "country": self.country,
            "lowestPrice": self.lowestPrice,
            "currency": self.currency,
            "flightDate": self.flightDate
        }