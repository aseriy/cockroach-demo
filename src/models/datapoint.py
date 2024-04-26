from pydantic import BaseModel
from datetime import datetime


class DataPoint(BaseModel):
  station: str
  date: datetime
  param0: int
  param1: int
  param2: float
  param3: float
  param4: str

