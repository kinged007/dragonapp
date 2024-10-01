from nicegui import ui, APIRouter, app
from core.utils.string import to_snake_case
from core import Module
from core.utils.database import Database
from core.schemas.database import DatabaseMongoBaseModel

# Import Theme and Common Elements
from ..common.theme import get_theme
from core.utils.frontend.crud import CrudBuilder
from core.utils.frontend import ui_helper

router = APIRouter()

@router.page('/{tool_name}')
async def module_page(tool_name:str):
    Theme = get_theme()
    
    with Theme.frame('Tool: ' + tool_name):
        ui.label('Tool page!')
        
        match tool_name:
            case 'app-explorer':
                from .appexplorer import app_explorer
                await app_explorer()
            case 'create':
                ui.label('Create a tool')
            case 'update':
                ui.label('Update a tool')
            case 'delete':
                ui.label('Delete a tool')
            case _:
                ui.label('Unknown action')

        # NOTE dark mode will be persistent for each user across tabs and server restarts
        ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
        ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
        
# @router.page('/{tool_name}')
# async def db_page(tool_name:str):
#     Theme = get_theme()
        
#     with Theme.frame(f'Tool: {tool_name}'):
            
            
#             return