import asyncio, time
from core.utils.frontend import ui_helper, ui, FormBuilder
from core.utils.database import Database, ObjectId
from core.utils.datetime import nice_time
from core import log, print
from ..schema import Tenant, Status, MigrationJob, MigrationOptions
from ..src import utils, msapp
from ..schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions, AppsType
from ..src.migration import save_execution


def migration_tab_execute(migration_job:MigrationJob, source_tenant: Tenant = None):
    # Migration callback

    migrating_in_progress = {'value': False}
    
    def _log(msg):
        output_log.push(f"{nice_time()} | {msg}")
        migration_job.log.append(f"{nice_time()} | {msg}")
        print(msg)
    
    async def _process_migration():
        n = ui.notification(timeout=None)
        try:
            data = await migration_options.run_editor_method('get')
            await asyncio.sleep(0.1)
            migration_job.migration_options = MigrationOptions(**data.get('json',{})) 
            
            n.spinner = True
            migrating_in_progress.update(value=True)
            
            _log("Starting Migration Job...")
            for k,v in migration_job.model_dump().items():
                if k in ['app_id_mapping', 'apps_failed', 'log', '_id']:
                    continue
                if k == 'apps': v = [{app['appId']: app['displayName']} for app in v]
                if k in ['source_tenant','destination_tenants']:
                    v = [v] if not isinstance(v, list) else v
                    v = [{t.get("name"): t.get("client_id")} for t in v]
                    
                _log(f"{k}: {v}")
                
            await asyncio.sleep(5)
            for _c in range(10):
                output_log.push(f"Starting Migration Job in ... {_c}/10")
                await asyncio.sleep(1)
                if _cancel_button == False or migrating_in_progress.get('value',False) == False:
                    output_log.push(f"Migration Cancelled.")
                    migrating_in_progress.update(value=False)
                    break
            
            if not migrating_in_progress.get('value',False): 
                n.message = "Cancelled"
                n.spinner = False
                n.dismiss()
                _log("Migration Job Cancelled.")
                ui.notify("Migration Job Cancelled", type='negative')
                return
            
            ### Migrate Apps
            if migration_job.stage == 'apps':
                
                _log("Executing App Migration...")
                async for result in msapp.process_migration_job(migration_job):
                    _log(migration_job.apps_type + " | " + result)
                
                _log("Migration of Apps is Complete.")
                _log(f"Execution status: {migration_job.status}")
                
                if migration_job.status == Status.COMPLETED:
                    migration_job.stage = 'post_apps'
                    
                # Update
                save_execution(migration_job)
            
            ### Post Process Apps
            if migration_job.stage == 'post_apps':
                
                await asyncio.sleep(2)
                _log("Post Processing Newly Migrated Apps...")
                # migration_job.status = Status.IN_PROGRESS
                async for result in msapp.post_process_migration_job(migration_job):
                    _log(migration_job.apps_type + " | " + result)
            
                _log("Post Processing Newly Migrated Apps is Complete...")
                _log(f"Execution status: {migration_job.status}")
                
                if migration_job.status == Status.COMPLETED and migration_job.migration_options.migrate_service_principals:
                    migration_job.stage = 'service_principals_from_apps'
                
                # Update
                save_execution(migration_job)

            ### Fetch Service Principals based on migrated Apps
            if migration_job.stage == 'service_principals_from_apps':
                
                await asyncio.sleep(2)
                migration_job.apps_type = AppsType.servicePrincipals # Change this so we continue from the correct point
                async for result in msapp.process_service_principal_migration(migration_job, source_tenant):
                    _log(migration_job.apps_type + " | " + result)
                
                if migration_job.status == Status.COMPLETED:
                    migration_job.stage = 'service_principals'
                
                # Update
                migration_job.status = Status.IN_PROGRESS # DEBUG
                save_execution(migration_job)
            
            ### Migrate Service Principals
            if migration_job.stage == 'service_principals':
                
                _log("Executing Service Principal Migration.")
                await asyncio.sleep(2)
                migration_job.apps_type = AppsType.servicePrincipals # Change this so we continue from the correct point
                async for result in msapp.process_migration_job(migration_job):
                    _log(migration_job.apps_type + " | " + result)
                _log("Service Principal Migration is Complete.")
                _log(f"Execution status: {migration_job.status}")
                
                if migration_job.status == Status.COMPLETED:
                    migration_job.stage = 'post_service_principals'
                
                # Update
                save_execution(migration_job)
                
            ### Post Process Service Principals
            if migration_job.stage == 'post_service_principals':
                    
                _log("Post Processing Newly Migrated Service Principals...")
                await asyncio.sleep(2)
                async for result in msapp.post_process_migration_job(migration_job):
                    _log(migration_job.apps_type + " | " + result)
                _log("Post Processing Newly Migrated Service Principals is Complete...")
                _log(f"Execution status: {migration_job.status}")
                
                if migration_job.status == Status.COMPLETED:
                    migration_job.stage = 'completed'
                
                # Update
                save_execution(migration_job)
                
                
                
            n.message = "Migration Job Execution Completed"
            n.icon = 'check'
            n.spinner = False
            n.type = 'positive'
            await asyncio.sleep(1)
            n.dismiss()
            if migration_job.status == Status.COMPLETED:
                ui.notify("Migration Job Completed", type='positive')
                execute_button.disable()
            else:
                ui.notify("Migration Job Execution is finished, but not complete.", type='negative')
                
            # ui.notify("Migration Job Executed", type='positive')
            # Job is saved in  the execution method
            _log("Migration Job Execution Completed.")
            migrating_in_progress.update(value=False)
            
            
            
        except Exception as e:
            _log(f"Error: {e}")
            n.dismiss()
            ui.notify(f"Error: {e}", type='negative')                
    
    # Re-fetch the migration job
    
    # get the migration_job
    # migration_job = db_client.find_one({'_id': ObjectId(migration_job.id)})
    # migration_job = MigrationJob(**migration_job)
    _ready = True
    
    # Process
    # 1. Check status is correct
    if migration_job.status not in [Status.APPROVED, Status.IN_PROGRESS, Status.CANCELLED, Status.FAILED]:
        ui_helper.alert_error(f"Migration Job cannot be Executed. Current status: {migration_job.status}")
        _ready = False
    
    # 2. Check source_tenant exists and destination tenants exist
    # DEPRECATED - not using source tennats anymore. use app explorer
    # if not migration_job.source_tenant:
    #     ui_helper.alert_error(f"Source Tenant not set.")
    #     _ready = False
        
    if not migration_job.destination_tenants:
        ui_helper.alert_error(f"Destination Tenants not set.")
        _ready = False
    
    # 3. Check apps to migrate
    if not migration_job.apps:
        ui_helper.alert_error(f"No Apps to migrate.")
        _ready = False

    if _ready:
        
        ui.label("Migration Summary").classes('font-bold text-lg')
        ui.separator()
        ui.label(f"Migration Job: {migration_job.name}")
        ui.label(f"Status: {migration_job.status}")
        ui.label(f"Stage: {migration_job.stage.capitalize()}")
        ui.label(f"Approved by: TODO")
        ui.label(f"Approved on: TODO")
        ui.separator()
        ui.label(f"Source Tenant: {migration_job.name}")
        ui.label(f"Destination Tenants: {', '.join([t.name for t in migration_job.destination_tenants])}")
        ui.label("Migration Options")
        migration_options = ui.json_editor({'content':{'json': migration_job.migration_options.model_dump()}})
        ui.separator()
        ui.label(f"Apps to Migrate: {len(migration_job.apps)}")
        ui.label(f"Apps Type: {migration_job.apps_type}")
        ui.separator() 
        # ui.label("Apps Migrated")
        # ui.json_editor({'content':{'json': migration_job.app_id_mapping}})
        
        with ui.row():
            execute_button = ui.button("Execute Migration", on_click=_process_migration ).classes("bg-positive text-white")
            ui.button("Execute Post-Processing Migration" )
            ui.button("View Report" )
            # ui.button("Cancel Migration", on_click=lambda: ui.navigate.to(f"ms_entra/migrate-job/{migration_job.id}?tab=report") ).bind_visibility_from(locals(),'migrating_in_progress')
            _cancel_button = ui.button("Cancel Migration", on_click=lambda: migrating_in_progress.update(value=False) ).classes("bg-negative text-white").bind_visibility_from(migrating_in_progress, 'value')
        
        ui.label("Migration Execution Log")
        ui.separator()
        output_log = ui.log().classes('w-full full-width h-300')   