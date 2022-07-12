import enum
from typing import Any, Dict, List, Optional
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
    room: Optional[str] = None
    freq: str = "1D"

class FeedbackTimelineResponse(pydantic.BaseModel):
    dt: List[datetime]
    measure: List[str]
    room: List[str]
    value_min: List[float]
    value_mean: List[float]
    value_max: List[float]
    value_std: List[float]
    value_count: List[float]
    
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
    value_count: List[float]
    
class MergedTimelineResponse(pydantic.BaseModel):
    dt: List[datetime]
    measure: List[str]
    room: List[str]
    value_min_sensor: List[float]
    value_mean_sensor: List[float]
    value_max_sensor: List[float]
    value_std_sensor: List[float]
    value_count_sensor: List[float]
    value_min_vote: List[float]
    value_mean_vote: List[float]
    value_max_vote: List[float]
    value_std_vote: List[float]
    value_count_vote: List[float]

class CorrelationMatrixResponse(pydantic.BaseModel):
     __root__: Dict[str, Dict[str, float]]

class MLDataRequest(pydantic.BaseModel):
    ini_date: date
    end_date: date
    measure: Optional[str] = None
    room: Optional[str]
    freq: str = "1D"
     
class LogisticRegressionParameters(MLDataRequest):
    test_size: float = 0.3

class LogisticRegressionMeasure(pydantic.BaseModel):
    accuracy: float
    mse: float
    model: dict

class LogisticRegressionResponse(pydantic.BaseModel):
    __root__: Dict[str, LogisticRegressionMeasure]
