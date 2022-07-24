import enum
from typing import Any, Dict, List, Literal, Optional, Union

from datetime import date, datetime

import pydantic

import analysis.config as cfg
from analysis.feedback.models import CategoriesEnum

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
    message: Union[str, dict]
    
class RoomList(pydantic.BaseModel):
    rooms: List[str]

class MeasureList(pydantic.BaseModel):
    measures: List[str]

class DateRange(pydantic.BaseModel):
    min_date: datetime
    max_date: datetime
    
class FeedbackTimelineRequest(pydantic.BaseModel):
    ini_date: date
    end_date: date
    measures: Optional[List[str]] = pydantic.Field(default=None)
    rooms: Optional[List[str]] = pydantic.Field(default=None)
    freq: str = "1D"

    class Config:
        schema_extra = {
            'example': {
                    'ini_date': datetime.now().date(),
                    'end_date': datetime.now().date(),
                    'measures': ['noise'],
                    'rooms': ['CIC-4', '3203'],
                    'freq': '1D'
            }
        }

class FeedbackTimelineResponse(pydantic.BaseModel):
    dt: List[datetime]
    measure: List[str]
    room: List[str]
    value_min: List[float]
    value_mean: List[float]
    value_max: List[float]
    value_std: List[float]
    value_count: List[float]

    class Config:
        schema_extra = {
            'example': {
                "dt": [ "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00", "2022-03-02T00:00:00" ],
                "measure": [ "co2", "co2", "humidity_cold", "humidity_cold", "humidity_hot", "luminosity", "luminosity", "noise", "noise", "temperature_cold", "temperature_cold", "temperature_hot", "humidity_hot", "temperature_hot" ],
                "room": [ "3203", "CIC-4", "3203", "CIC-4", "3203", "3203", "CIC-4", "3203", "CIC-4", "3203", "CIC-4", "3203", "CIC-4", "CIC-4" ],
                "value_min": [ 3, 2, 1, 2, 2, 1, 3, 3, 5, 1, 2, 2, 3, 3 ],
                "value_mean": [ 3.6666666666666665, 3.5, 1.3333333333333333, 2, 2, 3, 4, 3.8333333333333335, 5, 1.3333333333333333, 2, 2, 3, 3 ],
                "value_max": [ 4, 5, 2, 2, 2, 5, 5, 5, 5, 2, 2, 2, 3, 3 ],
                "value_std": [ 0.5773502691896258, 2.1213203435596424, 0.5773502691896257, 0, 0, 1.6035674514745466, 1, 0.752772652709081, 0, 0.5773502691896257, 0, 0, 3, 3 ],
                "value_count": [ 3, 2, 3, 2, 2, 8, 3, 6, 3, 3, 2, 2, 3, 3 ]
            }
        }
    
class SensorizationTimelineRequest(pydantic.BaseModel):
    ini_date: date
    end_date: date
    measures: Optional[List[str]] = pydantic.Field(default=None)
    rooms: Optional[List[str]] = pydantic.Field(default=None)
    freq: str = "1D"

    class Config:
        schema_extra = {
            'example': {
                    'ini_date': datetime.now().date(),
                    'end_date': datetime.now().date(),
                    'measures': ['noise'],
                    'rooms': ['CIC-4', '3203'],
                    'freq': '1D'
            }
        }
    
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
    measure: Optional[List[str]] = None
    room: Optional[List[str]]
    freq: str = "1D"

    class Config:
        schema_extra = {
            'example': {
                    'ini_date': datetime.now().date(),
                    'end_date': datetime.now().date(),
                    'measure': ['noise'],
                    'room': ['CIC-4', '3203'],
                    'freq': '1D'
            }
        }
    
class LogisticRegressionParameters(MLDataRequest):
    test_size: float = 0.3
    penalty: Optional[Literal['none','l2','l1','elasticnet']] = pydantic.Field('l2', desciption='Specify the norm of the penalty')
    C: Optional[float] = pydantic.Field(1e10, description='Inverse of regularization strength; must be a positive float. Like in support vector machines, smaller values specify stronger regularization.', gt=0)
    l1_ratio: Optional[float] = pydantic.Field(0.0, description="The Elastic-Net mixing parameter, with 0 <= l1_ratio <= 1. Only used if penalty='elasticnet'. Setting l1_ratio=0 is equivalent to using penalty='l2', while setting l1_ratio=1 is equivalent to using penalty='l1'. For 0 < l1_ratio <1, the penalty is a combination of L1 and L2.", ge=0, le=1)
    max_iter: Optional[int] = 1000
    
class LogisticRegressionMeasure(pydantic.BaseModel):
    accuracy: float
    mse: float
    features: List[str]
    model: dict

class LogisticRegressionResponse(pydantic.BaseModel):
    models: Dict[str, LogisticRegressionMeasure]
    errors: Dict[str, str]
