import enum
from typing import Any, List, Optional
from typing_extensions import Annotated

from datetime import date, datetime, timedelta

import dateparser

import pydantic

import numpy as np

import analysis.config as cfg
from analysis.feedback.models import CategoriesEnum
from analysis.sensors.mg_source import GROUP_SENSORS_USING_TYPE

def pythonic_name(string: str) -> str:
    return string.replace(' ', '_')

CategoryKind = enum.Enum('Category', {pythonic_name(i.name): i.name for i in CategoriesEnum.all_categories()})
MeasureKind = enum.Enum('Measure', {pythonic_name(name): name for name in cfg.get_all_measures()})


class ConfigResponse(pydantic.BaseModel):
    datasources: cfg.DataSourceType
    cluster: cfg.ClusterType
    data: cfg.AnalysisDataType
    cache: cfg.CacheType

class ErrorResponse(pydantic.BaseModel):
    error: str
    message: Any
    
class RoomList(pydantic.BaseModel):
    rooms: List[str]

class MeasureList(pydantic.BaseModel):
    measures: List[str]

class FeedbackTimelineRequest(pydantic.BaseModel):
    ini_date: date
    end_date: date
    measure: Optional[str] = None
    room: Optional[str]
    freq: str = "1D"

class FeedbackTimelineResponse(pydantic.BaseModel):
    dt: List[datetime]
    measure: List[str]
    room: List[str]
    value_min: List[float]
    value_mean: List[float]
    value_max: List[float]
    value_std: List[float]

class SensorizationTimelineRequest(pydantic.BaseModel):
    ini_date: date
    end_date: date
    measure: Optional[str] = None
    room: Optional[str] = None
    freq: str = "1D"
    
class SensorizationTimelineResponse(pydantic.BaseModel):
    dt: List[datetime]
    measure: List[str]
    room: List[str]
    value_min: List[float]
    value_mean: List[float]
    value_max: List[float]
    value_std: List[float]


class AnalysisPeriodType(str, enum.Enum):
    HOURLY = 'hourly'
    DAYLY = 'dayly'
    MONTHLY = 'monthly'

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

class AnalysisRequestType(pydantic.BaseModel):
    period: AnalysisPeriodType
    category: CategoryKind
    group_by: GROUP_SENSORS_USING_TYPE
    
class AnalysisResponseType(pydantic.BaseModel):
    min_date: datetime
    max_date: datetime
    size: List[int]
    correlations: object
