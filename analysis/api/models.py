import enum
from typing import List
from datetime import datetime
import pydantic

class AnalysisPeriodType(enum.Enum):
    HOURLY = 'hourly'
    DAYLY = 'dayly'
    MONTHLY = 'monthly'

class AnalysisResultType(pydantic.BaseModel):
    min_date: datetime
    max_date: datetime
    shape: List[int]
    score: object
