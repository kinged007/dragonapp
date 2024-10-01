from core.types import SecretStr, Field, BaseModel, SecretStr, CronSchedule, EmailStr, AwareDatetime, condecimal
from core.schemas.module_config import BaseModuleConfig
from typing import Literal, Optional, List, Annotated
from importlib import import_module
from core.common import log
from .common.models import FrontendThemeBaseModel, Colors
from croniter import croniter
from enum import Enum
from datetime import datetime, timezone, timedelta


class Config(BaseModuleConfig):
    """
    Settings for the Frontend Panel module.
    """
    THEME: Literal['dash_ui'] = Field(default="dash_ui", description="The theme to use for the Frontend Panel")
    THEME_COLORS: Colors = Field(default=Colors(), description="The default Color configuration for the theme", format="color")

    __theme: FrontendThemeBaseModel = None # TODO test this
    def get_theme(self)->FrontendThemeBaseModel:
        try:
            if self.__theme: return self.__theme
            theme_module = import_module(f"app.modules.ms_entra_ui.themes.{self.THEME}")
            theme = getattr(theme_module, "Theme")
            self.__theme = theme()
            return self.__theme
        except Exception as e:
            log.error(f"Failed to load theme: {e}")
            raise e


