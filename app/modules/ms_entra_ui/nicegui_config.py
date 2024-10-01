from pydantic import BaseModel

class Config(BaseModel):
    """
    Settings for the frontend Panel module.
    """
    THEME: str = "dash_ui"
    STORAGE: str = "memory"
    SECRET:str = "pick your private secret here"