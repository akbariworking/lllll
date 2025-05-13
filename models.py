from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Union

@dataclass
class User:
    id: int
    username: str
    user_type: str
    profile_complete: bool

@dataclass
class GymDetails:
    id: int
    user_id: int
    gym_name: str
    license_verified: bool
    address: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None

@dataclass
class TrainerDetails:
    id: int
    user_id: int
    full_name: str
    certification_verified: bool
    specialization: Optional[str] = None
    experience: Optional[int] = None
    gym_id: Optional[int] = None
    gym_name: Optional[str] = None

@dataclass
class AthleteDetails:
    id: int
    user_id: int
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goals: Optional[str] = None
    medical_conditions: Optional[str] = None
    gym_id: Optional[int] = None
    gym_name: Optional[str] = None
    trainer_id: Optional[int] = None
    trainer_name: Optional[str] = None

@dataclass
class MembershipPlan:
    id: int
    gym_id: int
    plan_name: str
    duration: int
    price: float
    description: Optional[str] = None

@dataclass
class Membership:
    id: int
    athlete_id: int
    plan_id: int
    start_date: datetime
    end_date: datetime
    payment_status: str

@dataclass
class GymVisit:
    id: int
    athlete_id: int
    gym_id: int
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    gym_name: Optional[str] = None

@dataclass
class Review:
    id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    athlete_name: Optional[str] = None

@dataclass
class ChatMessage:
    id: int
    sender_id: int
    receiver_id: int
    message: str
    created_at: datetime
    read: bool = False

@dataclass
class SupportTicket:
    id: int
    athlete_id: int
    gym_id: int
    subject: str
    message: str
    status: str
    created_at: datetime
    athlete_name: Optional[str] = None
    gym_name: Optional[str] = None

@dataclass
class SupportResponse:
    id: int
    ticket_id: int
    responder_id: int
    message: str
    created_at: datetime
    username: Optional[str] = None
    user_type: Optional[str] = None

@dataclass
class Statistics:
    members_count: int = 0
    trainers_count: int = 0
    athletes_count: int = 0
    visits_count: int = 0
    avg_rating: float = 0
    avg_time: float = 0
