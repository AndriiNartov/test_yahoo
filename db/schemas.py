from typing import List
from pydantic import BaseModel
from datetime import date


class DayTradingRecord(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int

    class Config:
        orm_mode = True


class CompanyRecordsResponse(BaseModel):
    id: int
    ticker: str
    records: List[DayTradingRecord]

    class Config:
        orm_mode = True
