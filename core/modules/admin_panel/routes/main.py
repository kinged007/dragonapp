# from fastapi import APIRouter
from main import app as fastapi_app
from core.common import log, settings

from nicegui import ui, app, APIRouter


router = APIRouter() # Dummy router to allow for the initliazation of the NiceGUI 

# Import Theme and Common Elements
from ..common.theme import get_theme


# Import routes
from . import modules, config
from ..common.menu import sidebar_menu

# Include the routes
app.include_router(modules.router, prefix="/collection", dependencies=None, tags=["Modules"]) 
app.include_router(config.router, prefix="/config", dependencies=None, tags=["Config"])



@ui.page('/')
def show():
    
    Theme = get_theme()
    with Theme.frame('Home Page', sidebar_menu):
        
        ui.label('Hello, FastAPI!')

        # NOTE dark mode will be persistent for each user across tabs and server restarts
        ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
        ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
        ui.link('Modules', '/collection')
        ui.label("Config:" + str( Theme.colors))

        print(app)
        print(app.storage)
        

ui.run_with(
    fastapi_app,
    mount_path=settings.ADMIN_PANEL_STR,  # NOTE this can be omitted if you want the paths passed to @ui.page to be at the root
    storage_secret=settings.ADMIN_STORAGE_KEY,  # NOTE setting a secret is optional but allows for persistent storage per user
    favicon="🚀",
    title=f"{settings.PROJECT_NAME} - Admin Panel",
)
log.info("Admin Panel Active")