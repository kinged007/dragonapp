from typing import Dict
import asyncio 

from core.modules.admin_panel import AdminPanel, ui, APIRouter
from core.utils.database import Database, ObjectId
from core.common import log, print

from core.utils.string import to_snake_case
from core.utils.datetime import nice_time

from core.utils.frontend import ui_helper
from core.utils.frontend.form_builder import FormBuilder
from .src import utils, msapp
from .schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions

# router = AdminPanel.router()
router = APIRouter()



@AdminPanel.page('/execute/{id}', title='Migration Job', viewport='full') # kwargs for @router.page
async def migration_job_exec(id:str=123):
    
    # Set up DB client
    db_client = Database.get_collection('ms_entra_migration_job')
    
    # get the migration_job
    migration_job = db_client.find_one({'_id': ObjectId(id)})
    migration_job = MigrationJob(**migration_job)
    
    
    # Process
    # 1. Check status is correct
    if migration_job.status != Status.APPROVED:
        ui_helper.alert_error(f"Migration Job is not in APPROVED status. Current status: {migration_job.status}")
        return
    
    # 2. Check source_tenant exists and destination tenants exist
    if not migration_job.source_tenant:
        ui_helper.alert_error(f"Source Tenant not set.")
        return
    if not migration_job.destination_tenants:
        ui_helper.alert_error(f"Destination Tenants not set.")
        return
    
    # 3. Check apps to migrate
    if not migration_job.apps:
        ui_helper.alert_error(f"No Apps to migrate.")
        return
    
    # fallback  # TODO Should be a dict, not a list!!
    if isinstance(migration_job.source_tenant, list):
        log.error("Source Tenant is a list! Should be a dict")
        migration_job.source_tenant = migration_job.source_tenant[0]

    source_tenant = migration_job.source_tenant.name
    
    # 4. Prepare Migration Summary
    ui.label("Migration Summary")
    ui.separator()
    ui.label(f"Migration Job: {migration_job.name}")
    ui.label(f"Status: {migration_job.status}")
    ui.label(f"Source Tenant: {source_tenant}")
    ui.label(f"Destination Tenants: {', '.join([t.name for t in migration_job.destination_tenants])}")
    ui.separator()
    ui.label("Migration Options")
    ui.json_editor({'content':{'json': migration_job.migration_options.model_dump()}})
    ui.separator()
    ui.label(f"Apps to Migrate: {len(migration_job.apps)}")
    ui.label(f"Apps Type: {migration_job.apps_type}")
    ui.label("Apps")
    ui.json_editor({'content':{'json': migration_job.apps}})
    ui.separator()
    
    # 5. Execute Migration
    
    async def _process_migration():
        n = ui.notification(timeout=None)
        try:
            n.spinner = True
            output_log.push(f"{nice_time()} | Executing Migration...")
            await asyncio.sleep(1)
            
            async for result in msapp.process_migration_job(migration_job):
                output_log.push(f"{nice_time()} | {result}.")
            
            n.message = "Migration Job Executed"
            n.icon = 'check'
            n.spinner = False
            n.type = 'positive'
            await asyncio.sleep(1)
            n.dismiss()
            execute_button.disabled = True
            # ui.notify("Migration Job Executed", type='positive')
        except Exception as e:
            output_log.push(f"{nice_time()} | Error: {e}")
            n.dismiss()
            ui.notify(f"Error: {e}", type='negative')
    
    with ui.row():
        execute_button = ui.button("Execute Migration", on_click=_process_migration )
        ui.button("Execute Post-Processing Migration" )
        ui.button("View Report" )
    
    ui.label("Migration Progress")
    ui.separator()
    output_log = ui.log().classes('w-full h-100')