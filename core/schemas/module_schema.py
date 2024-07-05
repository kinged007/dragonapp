from typing import List, Optional, Tuple, Callable, Type, Union
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from .module_config import BaseModuleConfig
from bson import ObjectId

from core.schemas.database import DatabaseMongoBaseModel
from core.utils.logging import logger as log, print
from core.utils.database import Database


class ModuleDocument(DatabaseMongoBaseModel):
    module_name: str = None
    title: str = None
    version: Optional[str] | None = None
    config: Optional[dict] | None = None
    
    class Settings:
        name = "modules"
    

class ModuleSchema(BaseModel):
    model_config = {
        "arbitrary_types_allowed": True,
    }
    name:str # Required. Pass in "__name__" to get the package name.
    title:Optional[str] = None # Nice readable title of the module. If none is passed, it will generate one using the package name in snake case.
    config_class:Optional[Type[BaseModuleConfig]] = None # Use a BaseModel format.
    config: Optional[BaseModuleConfig] = None # An instance of config_class
    router:Optional[APIRouter] = None # FastAPI APIRouter. Define API docs parameters there
    roles:Optional[List[str]] = None # User roles used by this module. Same roles as other modules will not be duplicated.
    labels:Optional[List[str]] = None # Predefined labels that may be selected in the admin panel, and applied to a user.
    cron:Optional[callable] = None # When its execution time, job is sent to RQ worker
    database:Optional[List[object]] = None
    events: Optional[List[Tuple[str, Callable]]] = None # List of sets of two items: event name and callback function
    dependencies:Optional[Union[List[Depends], Depends]] = None 
    modules_required:Optional[List[str]] = None # List of module names. Do a dependency check and raise an error if missing dependencies.
    version:Optional[str] = None # If module version is different when the app loads, it will attempt to read the connected databases, through the new Documents (if changed). If there are any errors retrieving the data, then it will raise an error and say that a migration of data is required to continue.
    description:Optional[str] = None # Description of the module, used in the admin panel, under the title before the data.


    def fetch_config(self):
        """
        Fetch the configuration from the database and updates the attributes of the module.
        
        Returns:
            The configuration object
        """
        data = Database.get_collection('modules').find_one({"module_name": self.name})
        
        # print("FETCH CONFIG", data)
        if not data:
            # Create it.
            self.save_config()
        else:
            # Load it.
            self.config = self.config_class(**data.get('config')) if data.get('config') else None
        return self.config
    
    def save_config(self):
        """
        Save the configuration to the database
        """
        try:
            item = Database.get_collection('modules').find_one({"module_name": self.name})
            _data = ModuleDocument(
                module_name=self.name,
                title=self.title,
                version=self.version,
                config=self.config.model_dump() if self.config else None
            )
            if item:
                _data.id = ObjectId(item['_id'])
                # print(_data.id, item,  _data.model_dump_json())
                Database.get_collection('modules').update_one({'_id': _data.id}, {"$set": _data.model_dump_json()})
            else:
                Database.get_collection('modules').insert_one(_data.model_dump_json())
        except Exception as e:
            log.error(f"Error saving module config: {e}")
            raise e