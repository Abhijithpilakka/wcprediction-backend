from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


# ─── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    name: str
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = v.strip().replace(" ", "").replace("-", "")
        if not digits.isdigit() or len(digits) < 10:
            raise ValueError("Enter a valid mobile number (min 10 digits)")
        return digits

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v


class AuthResponse(BaseModel):
    token: str
    user: dict


# ─── Matches ─────────────────────────────────────────────────────────────────

class MatchCreate(BaseModel):
    team1: str
    team2: str
    kickoff_time: datetime
    stage: str
    multiplier: float = 1.0

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        valid = ["Group", "Round of 16", "Quarter Final", "Semi Final", "Final"]
        if v not in valid:
            raise ValueError(f"Stage must be one of: {valid}")
        return v

    @field_validator("multiplier")
    @classmethod
    def validate_multiplier(cls, v: float) -> float:
        valid = [1.0, 1.2, 1.5, 1.8, 2.5]
        if v not in valid:
            raise ValueError(f"Multiplier must be one of: {valid}")
        return v


class MatchUpdate(BaseModel):
    team1: Optional[str] = None
    team2: Optional[str] = None
    kickoff_time: Optional[datetime] = None
    stage: Optional[str] = None
    multiplier: Optional[float] = None


class ResultUpdate(BaseModel):
    team1_score: int
    team2_score: int

    @field_validator("team1_score", "team2_score")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Score cannot be negative")
        return v


# ─── Predictions ─────────────────────────────────────────────────────────────

class PredictionCreate(BaseModel):
    match_id: str
    predicted_team1_score: int
    predicted_team2_score: int

    @field_validator("predicted_team1_score", "predicted_team2_score")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Score cannot be negative")
        return v


# ─── Admin ───────────────────────────────────────────────────────────────────

class BanUserRequest(BaseModel):
    user_id: str
    banned: bool = True
