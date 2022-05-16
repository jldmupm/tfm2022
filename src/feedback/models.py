# -*- coding: utf-8 -*-
from enum import Enum
from typing import List, Optional, Sequence # pydantic doesn't allow varidic tuples
import datetime

import pydantic

MIN_SCORE = 1
MID_SCORE = 3
MAX_SCORE = 5

AvailableFieldsList = ['id', 'subjectId', 'room', 'date', 'duration', 'reasonsString', 'score', 'category', 'reason']

class BaseModelFrozen(pydantic.BaseModel):
    class Config:                                                               
        allow_mutation = False  
        frozen = True

class Category(BaseModelFrozen):
    "Store the definition of a single category"
    name: str  = pydantic.Field(description="Name of the category.")
    statement: str = pydantic.Field(description="Statment for the category")
    positive_values: List[str] = pydantic.Field(description="Positive values for the category.")
    negative_values: List[str] = pydantic.Field(description="Negative values for the category.")

    def is_reason(self, reason: str) -> bool:
        return reason in [*self.positive_values, *self.negative_values]
    
    def is_positive(self, reason: str) -> bool:
        return reason in self.positive_values

    def is_negative(self, reason: str) -> bool:
        return reason in self.negative_values


# TODO: create dinamically from yaml    
class CategoriesEnum(Enum):
    "Definitions of all the categories"
    ESTADO_FISICO = Category(
        name="Estado físico",
        statement="Mi estado físico ha sido bueno",
        positive_values=["Enérgico/a", "Normal"],
        negative_values=["Agotado/a", "Enfermo/a", "Con hambre o sed", "Con dolor de cuello", "Con dolor de cabeza", "Con dolor de espalda"])
    ESTADO_ANIMICO = Category(
        name="Estado anímico",
        statement="Mi estado anímico ha sido bueno",
        positive_values=["Eufórico/a", "Motivado/a", "Contento/a", "Normal"],
        negative_values=["Cansado/a", "Con ansiedad", "Agobiado/a", "Estresado/a", "Triste", "Aburrido/a"])
    TEMARIO = Category(
        name="Temario",
        statement="El temario impartido ha sido bueno",
        positive_values=["Interesante", "Muy práctico", "Material adecuado", "Temario bien estructurado"],
        negative_values=["Repetitivo", "Poco práctico", "Material limitado", "Temario denso"])
    DOCENTE = Category(
        name="Docente",
        statement="La mayor del docente ha sido buena",
        positive_values=["Paciencia", "Explicaciones entretenidas", "Buena actitud", "Buena organización", "Creatividad", "Dinamismo"],
        negative_values=["Poca paciencia", "Explicaciones aburridas", "Poca cooperación", "Mala organización", "Poca creatividad", "Poco dinamismo"])
    AMBIENTE = Category(
        name="Ambiente",
        statement="El ambiente ha sido bueno",
        positive_values=["Temperatura perfecta", "Sin ruido", "Iluminación correcta", "Ambiente agradable"],
        negative_values=["Demasiado calor", "Demasiado frío", "Demasiado ruido", "Poca luz", "Ambiente denso"])

    @classmethod
    def all_categories(cls):
        return [category.value for category in CategoriesEnum]

    @classmethod
    def get_by_name(cls, name) -> Optional[Category]:
        category_with_name= next(filter(lambda category: category.name == name, CategoriesEnum.all_categories()), None)
        return category_with_name if category_with_name else None

    @classmethod
    def get_by_statement(cls, statement) -> Optional[Category]:
        category_with_statement = next(filter(lambda category: category.statement == statement, CategoriesEnum.all_categories()), None)
        return category_with_statement if category_with_statement else None

    @classmethod
    def get_by_category_id(cls, category_id) -> Optional[Category]:
        return cls.get_by_name(category_id) or cls.get_by_statement(category_id)
    
class Vote(BaseModelFrozen):
    "Store a vote for a category"
    category: str
    reasonsList: Sequence[str]
    reasonsString: str
    score: pydantic.conint(ge=1, le=5)

    @pydantic.root_validator
    def all_reasons_must_be_congruent_with_the_score(cls, values):
        category = values.get('category', None)
        categoryInstance = CategoriesEnum.get_by_category_id(category)
        assert categoryInstance, "The category {category} was not defined."
        score = values.get('score', 0)
        reasonsList = values.get('reasonsList', ())
        if score < MID_SCORE:
            checker = categoryInstance.is_negative
        elif score > MID_SCORE:
            checker = categoryInstance.is_positive
        else:
            checker = categoryInstance.is_reason
        assert all([checker(value) for value in reasonsList]), f"{categoryInstance.name} with a score of {score} contains an invalid reason: {reasonsList}."
        return values
    
class Survey(BaseModelFrozen):
    "Store the data of a vote"
    date: datetime.datetime
    duration: int
    room: str
    subjectId: str
    votingTuple: Sequence[Vote]
