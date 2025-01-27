"""settings.py - Read and validate settings."""

from pathlib import Path
from tomllib import load
from typing import Optional

from pydantic import BaseModel, Field


class MapSpec(BaseModel):
    """Details of each map."""

    name: str
    northwest: tuple[float, float]
    southeast: tuple[float, float]
    zoom: int
    dataAttribute: Optional[str] = None
    tileURL: Optional[str] = None


class MapSettings(BaseModel):
    """Map settings."""

    saveTempData: bool
    dataAttribute: str
    tileURL: str
    specs: list[MapSpec]


__map_settings: MapSettings


def load_settings():
    """Load settings."""
    global __map_settings
    with open("src/settings.toml", "rb") as f:
        settings = load(f)
        # __map_settings = MapSettings(**settings["map"])
        __map_settings = MapSettings.model_validate(settings["map"])
        for spec in __map_settings.specs:
            if spec.tileURL is None:
                spec.tileURL = __map_settings.tileURL
            if spec.dataAttribute is None:
                spec.dataAttribute = __map_settings.dataAttribute


load_settings()


def get_map_settings() -> MapSettings:
    """Get map settings."""
    return __map_settings
