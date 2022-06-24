import enum
from typing import List
from datetime import datetime, timedelta

import dateparser

import pydantic

class AnalysisPeriodType(str, enum.Enum):
    HOURLY = 'hourly'
    DAYLY = 'dayly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'

    def get_period(self: str):
        if self == AnalysisPeriodType.HOURLY:
            end_at = dateparser.parse('1 hour ago').replace(minute=0, second=0, microsecond=0) - timedelta(seconds=1)
            start_at = dateparser.parse('2 hour ago').replace(minute=0, second=0, microsecond=0)
        elif self == AnalysisPeriodType.DAYLY:
            end_at = dateparser.parse('1 day ago').replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
            start_at = dateparser.parse('2 day ago').replace(hour=0, minute=0, second=0, microsecond=0)
        elif self == AnalysisPeriodType.MONTHLY:
            end_at = dateparser.parse('1 month ago').replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
            start_at = dateparser.parse('2 month ago').replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self == AnalysisPeriodType.YEARLY:
            end_at = dateparser.parse('now')
            start_at = dateparser.parse('1 year ago')
        else:
            raise ValueError(f'{self} No AnalysisResultType valid value')
        return (start_at, end_at)
        
class AnalysisResultType(pydantic.BaseModel):
    min_date: datetime
    max_date: datetime
    shape: List[int]
    score: object
