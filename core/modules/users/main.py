"""
This Users module extends the built in User module, and adds additional functionality to the user management system. It allows for the creation of new users, and the management of existing users. 
It also provides a way to assign roles to users, and to manage the permissions of those roles.
TODO Move this to app/modules/ - as it is a customizeable module.

"""


from core import Module
from .routes.users import router
from core import log

# Register the module in the app
Module.register(
    __name__,
    title = "Users",
    # slug = "users", # Automatically generated from the file path/folder name
    # config_class = 'MyModuleConfigClass', # Use a BaseModel format.
    router = router, # FastAPI APIRouter. Define API docs parameters there
    roles = ['my_unique_role','another_module_specific_role', 'editor'], # User roles used by this module. Same roles as other modules will not be duplicated.
    labels = ['predefined_label_option' ], # Predefined labels that may be selected in the admin panel, and applied to a user.
    # cron = 'my_cron_handler', # When its execution time, job is sent to RQ worker
    # database = ['MyModuleDatabaseDocument', 'AnotherModuleDatabaseDocument'],
    # frontend_routes = my_frontend_router # Creates frontend pages within a template, for this specific module, under the menu item of the modules name - can be configured from the frontend config page
    events = [
        ("hook.event.name", print ),
    ],
    # dependencies = ['users','ai','messaging'], # Do a dependency check and raise an error if missing dependencies.
    version = "0.0.3", # If module version is different when the app loads, it will attempt to read the connected databases, through the new Documents (if changed). If there are any errors retrieving the data, then it will raise an error and say that a migration of data is required to continue.
    # Auto migrations??? Or Migration scripts? Maybe a BaseModel that can be used to convert old column names to new column names, and define a default value if no value is found, if (for eg) no default value is defined in the Document schema.
    # migration situations: 
    #   1) Same database, new tables, different requirements/format.
    #   2) New database, same+new tables, different requirements
    # eg. Module.migrate(OldDatabase, NewDatabase, MigrationModel)
    # ...
    
)
           
print(__file__)
log.info(__file__)
# print(__path__)
print(__name__)
print(__package__)
