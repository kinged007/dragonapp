from core import Module
from core.config import settings

settings.APP_VERSION = "0.0.7" # not being used yet. Causes circular dependency when core/config.py imports it. TODO fix this

# Load core modules.
# Not importing users module, will ignore all user related calls and will disable user management from backend. All requests to create users etc will just return None
# ie. endpoints requiring user permissions will only work with API keys with relevant scopes.
# frontend core module is specifically designed to be used if app is a frontend app, not a backend.
# messaging core module handles push notifications, sms, email and IM messages (telegram, whatsapp,...). If app tries to send a message, an error will get logged
# ai core module includes computer vision, NLP and audio processing.
# locale core module offers translation capabilities. IF locale module is disabled, all strings will resort to their default values - ie. app base language is used.
Module.load_core(['admin_panel']) # ,'frontend','ai','messaging','locale'])

# Register modules with the app, so it will import it.
Module.load(['ms-entra'])
# Module.load(['bookshelf','ms-entra','pollygene'])
# Module.load(['my_module','entra-migrate','shlink','bookshelf'])
# Module.load()
# Modules.load('something_else') 

# Once all modules are loaded, it will do a dependency check. If a module is missing a dependency, it will raise an error.

# In essence, Now the app has been loaded. It will now start the server and listen for requests.
# If any custom code is required to be run before the server starts, it can be added here.
# All custom code should be placed inside a module endpoint or cron handler. Any utilities or models will be inside the module itself.


# Examples:
# - An API only webserver without AdminPanel will have all the code inside the module endpoints. CRUD operations, data processing, etc. 
# - An AdminPanel only webserver. If using a seperate backend, the baseurl must be defined so the panel may connect to the backend and make requests. The admin token and super admin login credentials should be identical as the backend. The Users module authorizes other users/api keys to access the admin panel.
# - A webserver with both API and AdminPanel. The AdminPanel will not make HTTP requests to the backend, instead it will interact with the database directly based on the module configurations.
# - Using teh AdminPanel as a customer App. Designed for more administrative type of apps (Like Directus). May be used for CMS, CRM, etc. The AdminPanel will have a user management system, roles, permissions, etc. The API will be used to interact with the frontend app. Modules may be used to extend the functionality of the AdminPanel.

# AdminPanel utilizes NiceGUI to create the frontend. The frontend is a SPA that interacts with the backend. 


# from .modules import my_module
