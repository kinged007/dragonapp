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

@router.page('/{module_name}')
def module_page(module_name:str):
    Theme = get_theme()
    
    with Theme.frame('Modules Page'):
        ui.label('Modules Page Again!')

        # NOTE dark mode will be persistent for each user across tabs and server restarts
        ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
        ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
        
@router.page('/{module_name}/{db_name}')
async def db_page(module_name:str, db_name:str):
    Theme = get_theme()
    
    if module_name in Module.loaded_modules:
        module = Module.modules[module_name]
        _title = module.title
    else:
        _title = to_snake_case(module_name)
        module = None

    db = None
    if module and module.database:
        for db in module.database:
            if issubclass(db, DatabaseMongoBaseModel):
                if db.Settings.name == db_name:
                    break

    if db:
        db_title = db.Settings.title if hasattr(db.Settings, 'title') else to_snake_case(db.Settings.name)
    else:
        db_title = to_snake_case(db_name)
        
    with Theme.frame(f'{_title}:{db_title}'):
        
        if not module:
            ui.notification(f"Module '{module_name}' not found!", position='center', type='negative', icon='error', timeout=None)
            return

        ui.label('Module Database: ' + db_title).classes('text-xl')
        if db:
            # Build a CRUD interface for the database
            """
            # Ideal Interface build....
            # Main compnents:
            # 1. Table
            # 2. Form
            # 3. Search
            # 4. Pagination
            # 5. Sorting
            # 6. Filters
            # 7. Export
            # 8. Import
            # 9. Delete
            # 10. Edit
            # 11. Add
            # 12. View
            # 13. Refresh
            # 14. Save
            # 15. Cancel
            # 16. Help
            # 17. Settings
            
            crud = CrudBuilder(db)
            with ui.row():
                crud.button_new( schema = different_model.model_json_schema() )
                crud.button_edit()
                crud.button_delete()
                ui.space()
                crud.search()
                crud.filter()
                crud.sort()
            
            crud.table(
                selectable = True, # adds checkboxes to each row
                columns = ['id','name','email',...],
                actions = ['edit','delete','view'], # or None to disable
            
            )
            crud.pagination()
            
            with ui.row():
                crud.button_refresh()
                crud.button_save()
                crud.button_cancel()
                crud.button_settings()
                ui.space()
                crud.export()
                crud.import()
            
            
            """
            ui.label("Building CRUD Interface...")
            ui.separator()
            # Build the CRUD interface using default layout
            crud = CrudBuilder(base_model=db, module_name=module_name).build()
        else:
            ui_helper.alert(f"Database '{db_name}' not found in module '{module_name}'!", position='center', type='negative', icon='error', timeout=None)
            return