from nicegui import ui, APIRouter, app
import json

from core.utils.string import to_snake_case
from core import Module, log
from core.schemas.database import DatabaseMongoBaseModel

# Import Theme and Common Elements
from ..common.theme import get_theme
from core.utils.frontend.crud import CrudBuilder
from core.utils.frontend import ui_helper
from core.utils.frontend.form_builder import FormBuilder

from core.utils.database import Database, ObjectId
from app.modules.ms_entra.src import utils, msapp
from app.modules.ms_entra.models import applications, service_principals
from app.modules.ms_entra.schema import Tenant, MigrationJob

router = APIRouter()

@router.page('/{action}')
def module_page( action:str = 'list'):
    Theme = get_theme()
    
    with Theme.frame(f'Tickets: {action}'):
        ui.label('Ticket page!')

        # NOTE dark mode will be persistent for each user across tabs and server restarts
        ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
        ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
        
@router.page('/view/{ticket}')
async def db_page(ticket:str, view:str="list"):
    Theme = get_theme()
    
    
    # Set up DB client
    db_client = Database.get_collection(MigrationJob.Settings.name)
    
    # get the migration_job
    migration_job = db_client.find_one({'_id': ObjectId(ticket)})
    migration_job = MigrationJob(**migration_job)
    
    def save_ticket(data):
        ui.notify("Saving Ticket")
        print(data)
        try:
            new_config = MigrationJob(**data)
            # Data validated
            migration_job = new_config
            db_client.update_one({'_id': ObjectId(ticket)}, new_config.model_dump())
            
        except Exception as e:
            raise Exception([str(er.get('loc')) + ": " +er.get('msg') for er in e.errors()])
            # print(type(e),e.errors(), e.title, e.args)
            raise e
        
        return True

    def form_builder(key, property):
        print(key, property)
        if key in ['apps_type','search_params','source_tenant','log']:
            return None, None
            
            
        return key, property
    
    with Theme.frame(f'Ticket: {migration_job.name} ({ticket})'):
        
        schema = migration_job.model_json_schema()
        with Theme.content("Overview"):
            
            with ui.tabs().classes() as tabs:
                # list = ui.tab('List')
                overview = ui.tab('Overview')
                edit = ui.tab('Edit')
                approve = ui.tab('Approve')
                apps = ui.tab('Apps')

            with ui.tab_panels(tabs, value=overview).props('q-pa-none').classes('full-width').style("background: none;"):

                with ui.tab_panel(overview).props('q-pa-none'):

                    ui.json_editor({ 'content' : {'json': migration_job.model_dump() }})
                
                with ui.tab_panel(edit):
                    
                    ui.label('Edit Ticket')
                    FormBuilder(schema, migration_job.model_dump(mode="json"), save_ticket ).build(form_builder)

                with ui.tab_panel(apps):
                    
                    def _validate_input(_d):
                        try:
                            if isinstance(_d, str):
                                _d = json.loads(_d)
                            if isinstance(_d, list):
                                _d = _d
                            elif isinstance(_d, dict):
                                _d = [_d]
                            else:
                                raise Exception("Invalid JSON App data!")
                        except Exception as e:
                            raise Exception("Invalid JSON App data!")
                        
                        return _d

                    async def validate_data():
                        
                        _d = await app_json.run_editor_method('get')
                        _dd = _d.get('json', []) if 'json' in _d else _d.get('text', "") if 'text' in _d else []
                        # Validate JSON
                        try:
                            d = []
                            if _dd:
                                _dd = _validate_input(_dd)
                                for d in _dd:
                                    d = applications.ApplicationModel(**d)
                                # _dd = applications.ApplicationModel(**_dd)
                                migration_job.apps = _dd
                        except Exception as e:
                            ui.notify(str(e))
                            return False

                        _d = await sp_json.run_editor_method('get')
                        _dd = _d.get('json', []) if 'json' in _d else _d.get('text', "") if 'text' in _d else []

                        # Validate JSON
                        try:
                            d = []
                            if _dd:
                                _dd = _validate_input(_dd)
                                for d in _dd:
                                    d = service_principals.ServicePrincipalModel(**d)
                                    # _dd = service_principals.ServicePrincipalModel(**_dd)
                                migration_job.service_principals = _dd
                        except Exception as e:
                            ui.notify(str(e))
                            return False

                        ui.notify("Validated")
                        return True
                        
                    async def update_json():
                        
                        if not await validate_data():
                            ui.notify("Not Saved")
                            return False
                        db_client.update_one({'_id': ObjectId(ticket)}, migration_job.model_dump())
                        ui.notify("Saved")
                    
                    ui.label('Applications')
                    app_json = ui.json_editor({ 'content' : {'json': migration_job.apps }})
                    ui.label('Service Principals')
                    sp_json = ui.json_editor({ 'content' : {'json': migration_job.service_principals }})
                    ui.button('Validate').on_click(validate_data)
                    ui.button('Save').on_click(update_json)
                                    
