from pydantic import BaseModel

class Config(BaseModel):
    """
    Settings for the Admin Panel module.
    """
    THEME: str = "dash_ui"
    STORAGE: str = "memory"
    SECRET:str = "pick your private secret here"