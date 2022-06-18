# -*- coding: utf-8 -*-
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field

from bson.objectid import ObjectId


LIST_OF_MEASURES = [
    "luminosity"
    "humidity"
    "room_temp"
    "add_temp"
    "surf_temp"
    "movement"
    "co2"
    "noise"
]


class SensorEntryDataType:
    luminosity: Optional[float]
    humidity: Optional[float]
    room_temp: Optional[float]
    add_temp: Optional[float]
    surf_temp: Optional[float]
    movement: Optional[int]
    co2: Optional[float]
    noise: Optional[float]
    

class SensorEntryType:
    _id: ObjectId
    time: datetime
    data: SensorEntryDataType
    room: str = Field(alias='class')
    hub: str
    node: str
