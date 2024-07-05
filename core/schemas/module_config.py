from pydantic import BaseModel, Field
from core.utils.logging import logger as log
import inspect
from os import path
from datetime import datetime, timezone

class BaseModuleConfig(BaseModel):
    """
    Base module configuration
    """
    # module_name:str = Field(default=None, description="The name of the module", init_var=True)
    _module_name: str
    _data: str
    
    def __init__(self, **data):

        # Convert all naive datetime objects in data to aware datetime objects
        for key, value in data.items():
            if isinstance(value, datetime) and value.tzinfo is None:
                data[key] = value.replace(tzinfo=timezone.utc)
                
        super().__init__(**data)
        
        # Get the file that contains the child class
        child_class_file = inspect.getfile(self.__class__)

        # Get the filename and directory
        filename = path.basename(child_class_file)
        directory = path.dirname(child_class_file)
        # self.module_name = path.basename(directory)        
        log.debug(f"Module Config Initialized: {path.basename(directory) }")
        self._module_name = path.basename(directory)
        self._data = data
        
