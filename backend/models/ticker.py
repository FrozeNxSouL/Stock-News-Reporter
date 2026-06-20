"""
Pydantic models for stock tickers.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TickerBase(BaseModel):
    symbol: str
    name: str = ""
    sector: str = ""
    active: bool = True


class TickerCreate(TickerBase):
    pass


class TickerUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    active: Optional[bool] = None


class TickerInDB(TickerBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TickerResponse(TickerBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
