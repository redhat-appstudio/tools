"""Snapshot model"""
from pydantic import BaseModel, ConfigDict, Field


class Component(BaseModel):
    """snapshot component model"""

    model_config = ConfigDict(frozen=True)

    container_image: str = Field(alias="containerImage")


class Snapshot(BaseModel):
    """snapshot model"""

    model_config = ConfigDict(frozen=True)

    components: list[Component]
