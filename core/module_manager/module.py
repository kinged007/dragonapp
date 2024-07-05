
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Union, List, Optional, Dict, Any, Type, Callable
from importlib import import_module
from beanie import Document
from core.schemas import module_schema, singleton , module_config
from core.utils.logging import logger as log, print
from core.utils.string import to_snake_case

from core.config import settings

class Module(metaclass=singleton.SingletonMeta):
    
    __module_core_loaded:bool = False
    __module_app_loaded:bool = False
    
    modules:dict = {}
    loaded_modules:list = []
    _module_events:dict = {} # dict of module_name: [ set( event_name, callback_function ), ...]
    """
    Event Hooks that have been registered by the modules and their callbacks. Dictionary format is as follows:
    {
        "module_name": [
            ("event_name", "callback_function"),
        ]
        ...
    }
    """
    _databases:list = []
    roles:list = []
    labels:list = []
    _cron:list = [] # list of dict: "module_name": "cron_handler"
    
    
    
    @classmethod
    def load_core(cls, module: Union[str, List] = [
        'users',
        # ...
    ]):
        """
        Imports core modules.
        
        Args:
            module (Union[str, List], optional): The module to import. By default, load all core modules.
        
        Returns:
            None
            
        Raises:
            Exception: Failed to load module.
            
        """
        if cls.__module_core_loaded:
            raise Exception("Core modules have already been loaded.")

        if isinstance(module, str):
            module = [module]
        try:
            for mod in module:
                log.debug("Importing Core Module: " + mod)
                mod = import_module(f"core.modules.{mod}.main")
        except Exception as e:
            raise Exception(f"Failed to load module {mod}: {e}")
        log.info("Core modules loaded: " + str(module))
        cls.__module_core_loaded = True

    @classmethod
    def load(cls, module: Union[str, List] = []):
        """
        Imports user created or non-core modules. After all modules are imported, it will conduct a dependency check. If a module is missing a dependency, it will raise an error.
        
        Args:
            modules (List[str]): The modules to import.
            
        Returns:
            None
            
        Raises:
            Exception: Failed to load module.
        """
        if cls.__module_app_loaded:
            raise Exception("App modules have already been loaded.")
        if not cls.__module_core_loaded:
            raise Exception("Core modules must be loaded first.")
        
        if isinstance(module, str):
            module = [module]
        try:
            for mod in module:
                log.debug("Importing App Module: "+ mod)
                mod = import_module(f"app.modules.{mod}.main")
        except Exception as e:
            raise Exception(f"Failed to load module {mod}: {e}")

        log.info("App modules loaded: " + str(module))

        cls.__module_app_loaded = True
        cls.__post_load_checks()

    @classmethod
    def __post_load_checks(cls):
        """
        Conducts post load checks on the modules. Checks for dependencies, and other requirements.
        
        Returns:
            None
        """
        try:
            # Remove duplicates
            cls._databases = list(set(cls._databases))
            cls.roles = list(set(cls.roles))
            cls.labels = list(set(cls.labels))
            cls._cron = list(set(cls._cron))
            
            # Check for missing dependencies
            _load_dependecy_failed = False
            for _, mod in cls.modules.items():
                _missing = []
                if mod.dependencies:
                    for dep in mod.dependencies:
                        if dep not in cls.loaded_modules:
                            _missing.append(dep)
                if _missing:
                    log.error(f"Module '{mod.name}' has a dependency on '{', '.join(_missing)}', which has not been loaded.")
                    _load_dependecy_failed = True
            if _load_dependecy_failed:
                raise Exception("Failed to load modules due to missing dependencies.")
                
            # Check for version mismatches
            # Check for database schema changes
            
            # DEBUG
            # print(cls._module_events,cls._databases,cls.roles,cls.labels,cls._cron)
            # print(cls.loaded_modules)
            pass
        except Exception as e:
            raise Exception(f"Post load checks failed: {e}")
    
    @classmethod
    def register(cls, 
            package_name:str, # Required. Pass in "__name__" to get the package name.
            title:Optional[str] = None, # Nice readable title of the module. If none is passed, it will generate one using the package name in snake case.
            config_class:Optional[Type[module_config.BaseModuleConfig]] = None, # Use a BaseModuleConfig format.
            router:Optional[APIRouter] = None, # FastAPI APIRouter. Define API docs parameters there
            roles:Optional[List[str]] = None, # User roles used by this module. Same roles as other modules will not be duplicated.
            labels:Optional[List[str]] = None, # Predefined labels that may be selected in the admin panel, and applied to a user.
            cron:Optional[callable] = None, # When its execution time, job is sent to RQ worker
            database:Optional[List[object]] = None,
            #:str frontend_routes = my_frontend_router # Creates frontend pages within a template, for this specific module, under the menu item of the modules name - can be configured from the frontend config page
            events:Optional[List[set]] = None, # List of sets of two items: event name and callback function
            modules_required:Optional[List[str]] = None, # List of module names. Do a dependency check and raise an error if missing dependencies.
            dependencies:Optional[Union[List[Depends], Depends]] = None,
            version:Optional[str] = None, # If module version is different when the app loads, it will attempt to read the connected databases, through the new Documents (if changed). If there are any errors retrieving the data, then it will raise an error and say that a migration of data is required to continue.
            api_version:Optional[int] = 1, # API version number
            description:Optional[str] = None, # Description of the module, used in the admin panel, under the title before the data.
            
            **kwargs
        ):
        """
        Registers a module with the app. This will register the app's name, routes, cron handler, and other relevant information.
        Uses ModuleSchema to define the module.

        Args:
            package_name (str): Required. Pass in "__name__" to get the package name.
            title (str): Nice readable title of the module. If none is passed, it will generate one using the package name in snake case.
            config (BaseModel): Use a BaseModel format.
            routes (APIRouter): FastAPI APIRouter. Define API docs parameters there.
            roles (List[str]): User roles used by this module. Same roles as other modules will not be duplicated.
            labels (List[str]): Predefined labels that may be selected in the admin panel, and applied to a user.
            cron (callable): When its execution time, job is sent to RQ worker.
            database (List[Document]): The Beanie Document classes that define the database schemas used by this module.
            events (List[set]): List of sets of two items: event name and callback function.
            modules_required: List of module names. Do a dependency check and raise an error if missing dependencies.
            dependencies (List[Depends] | Depends): Using FastAPI Depends method, to check for dependencies to module.
            version (str): If module version is different when the app loads, it will attempt to read the connected databases, through the new Documents (if changed). If there are any errors retrieving the data, then it will raise an error and say that a migration of data is required to continue.
            api_version (int): API version number.
            description (str): Description of the module, used in the admin panel, under the title before the data.
            
            **kwargs: Additional keyword arguments.
        
        Returns:
            None

        Raises:
            Exception: If the registration fails, it will raise an error.
        """        
        log.debug("Registering module: " + package_name)
        
        try:
            if "." in package_name:
                package_name = package_name.split("modules.")[1].split(".")[0]
            if not isinstance(package_name, str):
                raise Exception("Module name must be a string. Pass in __name__ to get the package name.")
            
            if package_name in cls.loaded_modules:
                raise Exception(f"Module {package_name} has already been registered.")
        except Exception as e:
            raise Exception(f"Failed to register module {package_name}: {e}")
        
        
        # prepare json for schema validation
        _json = {
            "name" : package_name,
            "title": title if title else to_snake_case(package_name),
            "config_class": config_class, # TODO populate config from config.py so module config is in one place
            "router": router, 
            "roles": roles,
            "labels": labels,
            "cron": cron,
            "database": database,
            "events": events,
            "dependencies": dependencies,
            "modules_required": modules_required,
            "version": version,
            "description": description,
            
        }
        try:
            _module = module_schema.ModuleSchema(**_json)
            if not _module.config and _module.config_class:
                _module.config = _module.config_class()
        except Exception as e:
            log.error(f"Failed to register module {package_name}: {e}")
            raise Exception(f"Failed to register module {package_name}: {e}")
        
        # print("ModuleSchema", _module)
        # Add module name to the list of registered modules
        cls.loaded_modules.append(package_name)
        cls.modules[package_name] = _module
        if events: cls._module_events[package_name] = events
        if database: cls._databases.extend(database)
        if roles: cls.roles.extend(roles)
        if labels: cls.labels.extend(labels)
        if cron: cls._cron.extend({package_name: cron})
        
        # print(cls._module_events,cls._databases,cls.roles,cls.labels,cls._cron)
        # if kwargs: log.warning(kwargs)
    
    @classmethod
    def find_event_callbacks(cls, event_name:str, module_name:str = None) -> List[Callable]:
        """
        Find all registered event callbacks for a specific event.
        
        Args:
            event_name (str): The event name to search for.
            
        Returns:
            List[Callable]: A list of all registered callbacks for the event.
        """
        _callbacks = []
        for mod, events in cls._module_events.items():
            for event in events:
                if module_name and mod == module_name:
                    if event[0] == event_name:
                        _callbacks.append(event[1])
                elif not module_name:
                    if event[0] == event_name:
                        _callbacks.append(event[1])
                        
        return _callbacks
    
    
    @classmethod
    def by_name(cls, package_name: str) -> module_schema.ModuleSchema:
        """
        Get a module registration object by name.
        
        Args:
            name (str): The name of the module or __name__ which will be parsed to get the module name.
            
        Returns:
            The module which was originally registered.
        """
        if "." in package_name:
            package_name = package_name.split("modules.")[1].split(".")[0]
        if not isinstance(package_name, str):
            raise Exception("Module name must be a string. Pass in __name__ to get the local package name.")
        if package_name not in cls.loaded_modules:
            raise Exception(f"Module {package_name} has not been registered.")
        return cls.modules[package_name]
    
    @classmethod
    def load_routes(cls, app: APIRouter):
        """
        Load all registered routers.
        
        Returns:
            None
        """
        for _, mod in cls.modules.items():
            try:
                if mod.router:
                    # pass
                    app.include_router(
                        mod.router, 
                        prefix=f"{settings.API_V1_STR.rstrip('/')}/{mod.name}", 
                        # prefix=f"{settings.API_VERSION_STR.rstrip('/').format(version=mod.version)}/{mod.name}", # TODO using module versioning
                        tags=[f"{mod.name.capitalize()}"]
                    )
            except Exception as e:
                log.error(f"Failed to load routes for module {mod.name}: {e}")
                raise Exception(f"Failed to load routes for module {mod.name}: {e}")