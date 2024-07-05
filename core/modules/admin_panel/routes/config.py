from nicegui import ui, APIRouter, app
from pydantic_core import ValidationError
from core.utils.string import to_snake_case
from core import Module
from core.common import log, print
from core.schemas.database import DatabaseMongoBaseModel

# Import Theme and Common Elements
from ..common.theme import get_theme
from core.utils.frontend.form_builder import FormBuilder

router = APIRouter()

# Main module config page

def module_menu():
    # Place Modules settings at bottom of sidebar
    # with ui.column().classes('full-width'):
        # with ui.expansion("Modules", icon="extension").classes('full-width text-light'):
    for name, module in Module.modules.items():
    # for module in Module.loaded_modules:
        # _module_name = to_snake_case(module)
        ui.menu_item(module.title, on_click=lambda module=name: ui.navigate.to(f"/config/module/{module}")).classes('full-width')
        

# Module config page - show all modules to select
@router.page('/module')
async def module_main_page():
    
    Theme = get_theme()
    
    with Theme.frame('Settings'):
        
        with Theme.content('Settings', "Module configuration settings.", module_menu):
        
            ui.label("Choose a module to configure.")
        

@router.page('/module/{module_name}')
async def module_config_page(module_name:str):
    
    Theme = get_theme()

    def save_config(data:dict):
        print('Saving Config:', data)
        # Save the config to the database
        # admin_panel_config.update(data)
        # admin_panel_config.save()
        try:
            new_config = module.config_class(**data)
            # Data validated
            module.config = new_config
            module.save_config()
        except ValidationError as e:
            raise Exception([str(er.get('loc')) + ": " +er.get('msg') for er in e.errors()])
            # print(type(e),e.errors(), e.title, e.args)
            raise e
        
        return True
    
    
    module = Module.by_name(module_name)
        
    with Theme.frame(f'{module.title} Config Page'):
    # with Theme.frame(f'{to_snake_case(module_name)} Config Page'):

        if module_name not in Module.modules:
            ui.notification(f"Module '{module_name}' not found!", position='center', type='negative', icon='error', timeout=None)
            return
        
        schema = {}
        if module.config_class:
            schema = module.config_class.model_json_schema()
        
        _description = schema.get('description', 'You can modify the module settings here.')
        
        with Theme.content('Settings', _description, module_menu):
            
            if not schema or not schema.get('properties'):
                ui.label(f"Module '{module_name}' has no config settings.")
                return
            # print("CURRENT VALUES", module.config.model_dump(mode="json"))
            # TODO BUG Config is not loading current values from DB! Fix this.
            FormBuilder(schema, module.config.model_dump(mode="json"), save_config ).build()
            