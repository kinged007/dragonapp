from nicegui import ui, APIRouter, app
from core.utils.string import to_snake_case
from core import Module, log
from core.utils.database import Database
from core.schemas.database import DatabaseMongoBaseModel

# Import Theme and Common Elements
from ..common.theme import get_theme
from core.utils.frontend.crud import CrudBuilder
from core.utils.frontend import ui_helper
from core.utils.frontend.form_builder import FormBuilder

from core.utils.database import Database, ObjectId
from app.modules.ms_entra.src import utils, msapp
from app.modules.ms_entra.schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions

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
            
            ui.json_editor({ 'content' : {'json': migration_job.model_dump() }})
            
            FormBuilder(schema, migration_job.model_dump(mode="json"), save_ticket ).build(form_builder)
