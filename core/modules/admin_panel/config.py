from core.types import SecretStr, Field, BaseModel, SecretStr, CronSchedule, EmailStr, AwareDatetime, condecimal
from core.schemas.module_config import BaseModuleConfig
from typing import Literal, Optional, List, Annotated
from importlib import import_module
from core.common import log
from .common.models import AdminThemeBaseModel, Colors
from croniter import croniter
from enum import Enum
from datetime import datetime, timezone, timedelta

## DEBUG
class Color(str, Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    
class Model(BaseModel):
    sample: str = "a sample"
    sample2: Optional[str] = None
    



class Config(BaseModuleConfig):
    """
    Settings for the Admin Panel module.
    """
    THEME: Literal['dash_ui'] = Field(default="dash_ui", description="The theme to use for the Admin Panel")
    THEME_COLORS: Colors = Field(default=Colors(), description="The default Color configuration for the theme", format="color")
    # Fetch theme specific settings and offer them as config options?
    # THEME_SETTINGS: self.THEME.get_settings() = Field(default=self.THEME.get_settings(), description="The default settings for the theme")
    STORAGE: Literal['memory','test'] = "memory"
    SECRET: str = "pick your private secret here"
    
    
    #### DEBUG : testing BaseModel exporting to JSON Schema
    MODULE_NAME:str = Field(default="Admin Panel", description="The name of the module", json_schema_extra={"format": "textarea", "type": "string"})
    BOOL_OPTIONS: bool = False
    
    # Define the module version
    # MODULE_VERSION: Annotated[Decimal, Field(1.1, description="The version of the module", example=1.1, gt=0.0, lt=10.0, multiple_of=0.01, title="Module Version", decimal_places=2)] | None = None
    MODULE_VERSION: Annotated[float, str] = Field(1.1, description="The version of the module", example=1.1, gt=0.0, le=10.0, multiple_of=0.01, title="Module Version")
    MODULE_VERSION2: condecimal(gt=0.0, le=10.0, max_digits=4, decimal_places=2) = Field(
        1.1,
        description="The version of the module",
        example=1.1,
        title="Module Version 2"
    )

    MODULE_VERSION_INT: Optional[int] = 1
    
    # Define the module description
    MODULE_DESCRIPTION:str = "Test Module"
    TEST_DATE:str = Field("2021-01-01", description="A test date field", json_schema_extra={"format": "date"})
    TEST_TIME: str = Field("12:00", description="A test time field", json_schema_extra={"format": "time"})
    TEST_DATETIME: AwareDatetime = Field(datetime.now(tz=timezone.utc), description="A test datetime field")
    TEST_DATETIME2: datetime = Field(datetime.now(tz=timezone.utc), description="A test datetime field")
    
    # Define the module author
    MODULE_AUTHOR:str = "Test Author"
    MODULE_AUTHORS: Optional[List[str]] = Field(None, description="A list of authors", example=["Author1", "Author2"])
    
    # Define the module author email
    MODULE_AUTHOR_EMAIL: Optional[EmailStr] = Field(default=None, min_length=3, max_length=254, example="email@example.com", description="The email address of the module author.")
    
    MY_DICT:dict = Field(default={"example":"value"}, description="A dictionary field", json_schema_extra={"format": "json"})
    
    # schedule: CronSchedule = Field("*/15 * * * *", description="Cron schedule for the module")
    # schedule2: CronSchedule = Field("*/11 * * * *", description="Cron schedule for the module")
    
    multiple_colors: List[Color] = Field(["red","green"], description="A list of colors", example=["red", "green"])
    one_color: Color = Field("red", description="One color", example="red")
    one_color2: Optional[Color] = Field("red", description="One color", example="red")
    one_color3: Optional[Color] = Field(None, description="One color", example="red")
    literal_color: Literal["red", "green", "blue"] = Field("green", description="One color", example="red")
    sample_model: Optional[Model] = Field(description="A sample model", default=Model())
    sample_model_list: Optional[List[Model]] = Field(default=None, description="Another sample model")
    # json_param: Json = Field(..., description="A json parameter")
    password: Optional[str] = Field(None, description="A secret password", format="password")
    
    __theme: AdminThemeBaseModel = None # TODO test this
    def get_theme(self)->AdminThemeBaseModel:
        try:
            if self.__theme: return self.__theme
            theme_module = import_module(f"core.modules.admin_panel.themes.{self.THEME}")
            theme = getattr(theme_module, "Theme")
            self.__theme = theme()
            return self.__theme
        except Exception as e:
            log.error(f"Failed to load theme: {e}")
            raise e


# admin_panel_config = Config() # TODO DEPRECATE