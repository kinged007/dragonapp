"""
Migration logic for the module. Used in an async function.
Accepts MigrationJob object as argument.
Yields Text/log entries to be displayed in the frontend.

- Check displayName does not exist
- create apps
- populate with metadata
- check for errors
- post-process apps

- check SP for duplicates
- create SP
- populate with metadata
- check for errors
- post-process SP

"""

from typing import Union
from ..schema import MigrationJob
from core.utils.datetime import nice_time
from ..src.migration import update_migration_object
from core import log, print
from ..schema import Tenant, Status, MigrationJob, MigrationOptions
from ..src import utils, msapp
from ..schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions, AppsType
import asyncio
from ..models.applications import ApplicationModel
from ..models.service_principals import ServicePrincipalModel
from ..src.msapp import connect_tenant, server_request
from core.utils.frontend import ui_helper, ui, FormBuilder
from ..src import migrate_utils as mu



async def migrate_ui(job: MigrationJob):
    """
    Simply the UI that executes the migration process and updates the UI.
    """
    
    output_log = {}
    migrating_in_progress = {'value': False}
    _ready = True

    def _log(msg, append_log=True):
        """ Log a message to the console and the migration job log. """
        _m = f"{msg}"
        if append_log:
            _m = f"{nice_time()} | {msg}"
            job.log.append(_m)
            print(_m)
        output_log.push(_m)
        # yield _m
        
    async def migrate_start():
        n = ui.notification(timeout=None)
        try:
                        
            n.spinner = True
            migrating_in_progress.update(value=True)
            
            _log("Starting Migration Job...", append_log=True)
            for k,v in job.model_dump().items():
                if k in ['app_id_mapping', 'apps_failed', 'log', '_id']:
                    continue
                if k == 'apps': v = [app['displayName'] for app in v]
                if k in ['source_tenant','destination_tenants']:
                    v = [v] if not isinstance(v, list) else v
                    v = [t.get("name") for t in v if t]
                    
                _log(f"{k}: {v}", append_log=True)
                
            await asyncio.sleep(5)
            for _c in range(3): # DEBUG: Change to 10
                output_log.push(f"Starting Migration Job in ... {_c}/10")
                await asyncio.sleep(1)
                if _cancel_button == False or migrating_in_progress.get('value',False) == False:
                    output_log.push(f"Migration Cancelled.")
                    # migrating_in_progress.update(value=False)
                    break
            
            if not migrating_in_progress.get('value',False): 
                n.message = "Cancelled"
                n.spinner = False
                n.dismiss()
                _log("Migration Job Cancelled.", append_log=True)
                ui.notify("Migration Job Cancelled", type='negative')
                return

            # Update
            update_migration_object(job)

            ### Execute migration
            async for result in migrate_execution(job):
                _log(result, append_log=False)
            
            ### Finish up the migration            
            n.message = "Migration Job Execution Finished"
            n.icon = 'check'
            n.spinner = False
            n.type = 'positive'
            await asyncio.sleep(1)
            n.dismiss()
            if job.status == Status.COMPLETED:
                ui.notify("Migration Job Completed", type='positive')   
                execute_button.disable()
            else:
                ui.notify("Migration Job Execution is finished, but with errors.", type='negative')
                
            # ui.notify("Migration Job Executed", type='positive')
            # Job is saved in  the execution method
            _log("Migration Job Execution Completed.", append_log=True)
            migrating_in_progress.update(value=False)
            
        except Exception as e:
            _log(f"Error: {e}", append_log=True)
            n.dismiss()
            ui.notify(f"Error: {e}", type='negative')          
    
    # Process
    # 1. Check status is correct
    if job.status not in [Status.APPROVED, Status.IN_PROGRESS, Status.CANCELLED, Status.FAILED]:
        ui_helper.alert_error(f"Migration Job cannot be Executed. Current status: {job.status}")
        _ready = False
    
    # 2. Check source_tenant exists and destination tenants exist
    # DEPRECATED - not using source tennats anymore. use app explorer
    # if not job.source_tenant:
    #     ui_helper.alert_error(f"Source Tenant not set.")
    #     _ready = False
        
    if not job.destination_tenants:
        ui_helper.alert_error(f"Destination Tenants not set.")
        _ready = False
    
    # 3. Check apps to migrate
    if not job.apps:
        ui_helper.alert_error(f"No Apps to migrate.")
        _ready = False

    if _ready:
        
        ui.label("Migration Summary").classes('font-bold text-lg')
        ui.separator()
        ui.label(f"Migration Job: {job.name}")
        ui.label(f"Status: {job.status}")
        ui.label(f"Stage: {job.stage.capitalize()}")
        ui.label(f"Approved by: {job.approved_by}")
        ui.label(f"Approved on: {job.approved_at}")
        ui.separator()
        ui.label(f"Source Tenant: {job.name}")
        ui.label(f"Destination Tenants: {', '.join([t.name for t in job.destination_tenants])}")
        ui.label("Migration Options")
        ui.label("* Changes are not used.")
        migration_options = ui.json_editor({'content':{'json': job.migration_options.model_dump()}})
        ui.separator()
        ui.label(f"Apps to Migrate: {len(job.apps)}")
        ui.label(f"Apps Type: {job.apps_type}")
        ui.separator() 
        # ui.label("Apps Migrated")
        # ui.json_editor({'content':{'json': job.app_id_mapping}})
        
        with ui.row():
            execute_button = ui.button("Execute Migration", on_click=migrate_start ).classes("bg-positive text-white")
            # ui.button("Execute Post-Processing Migration" )
            # ui.button("View Report" )
            # ui.button("Cancel Migration", on_click=lambda: ui.navigate.to(f"ms_entra/migrate-job/{job.id}?tab=report") ).bind_visibility_from(locals(),'migrating_in_progress')
            _cancel_button = ui.button("Cancel Migration", on_click=lambda: migrating_in_progress.update(value=False) ).classes("bg-negative text-white").bind_visibility_from(migrating_in_progress, 'value')
        
        ui.label("Migration Execution Log")
        ui.separator()
        output_log = ui.log().classes('w-full full-width h-300')      
        
    else:
        
        ui.label("Migration Summary").classes('font-bold text-lg')
         
    
async def migrate_execution(job: MigrationJob):
    """
    Migration execution method to handle the migration process for both UI and background executions. 
    """

    def _log(msg):
        """ Log a message to the console and the migration job log. """
        _m = f"{nice_time()} | {msg}"
        job.log.append(_m)
        print(_m)
        return _m
    
    def _error(msg):
        """ Log an error message to the console and the migration job log. """
        job.error_log.append(f"{nice_time()} | ERROR: {msg}")
        return _log(f"ERROR: {msg}")


    tenants = []
    
    for dest in job.destination_tenants:
        
        try:
            
            _dest_tenant:Tenant = connect_tenant(dest.model_dump())
                        
            if not _dest_tenant.access_token:
                raise 
            
            tenants.append(_dest_tenant)
            
        except Exception as e:
            # raise Exception(f"Failed to connect to destination tenant: {dest.name}")
            yield _log(f"❌ Failed to connect to destination tenant: {dest.name}")
    
    for dest_tenant in tenants:
        
        # type declaration
        dest_tenant: Tenant
        
        yield _log(f"Connecting to {dest_tenant.name}")
        await asyncio.sleep(0.5)
        job.status = Status.IN_PROGRESS
        
        try:
            
            # migrate apps
            async for res in migrate_apps_to_tenant(job, dest_tenant):
                yield _log(res)
                            
            # migrate service principals
            
            
            # Prepare Report
            # Include a summary of the migration job
            # Include passwords and secrets (CSV)
            # Include IdP metadata (SAML) (XML)
            
            
            
            
            
            
            # Migrate apps
            # apps = job.apps if job.apps_type == AppsType.applications else job.service_principals
            # job.status = Status.IN_PROGRESS

            # yield _log(f"Migrating '{len(apps)}' '{job.apps_type}' to '{dest_tenant.name}'")
            # await asyncio.sleep(1)
                

            # for i in range(len(apps)):
                
            #     ### Validate App Data
                
            #     try:
                    
            #         yield _log(f"Parsing {job.apps_type} app data for {apps[i].get('displayName','?')}")
            #         await asyncio.sleep(0.3)
            #         # console.print(apps[i])
            #         if job.apps_type == AppsType.applications:
            #             _data = ApplicationModel(**apps[i])
            #         elif job.apps_type == AppsType.servicePrincipals:
            #             _data = ServicePrincipalModel(**apps[i])
            #         else:
            #             raise Exception("Error in table format. Invalid AppsType")
            #         # console.print(_data.post_model())
                    
            #     except Exception as e: 
            #         yield f"❌ Failed to parse app data for {apps[i].get('displayName','?')}: {e}"
            #         await asyncio.sleep(0.1)
            #         continue
                
            #     source_app_data = _data.model_copy()
                
                ### Manipulate App Data
                # Set naming convention
                # 

            
                ### Create App
                # Check if app is already migrated. If yes, then Update!
                
                
                ### Update Metadata
                
                
                
        except Exception as e:
            yield _log(f"❌ Failed: {e}")
            job.status = Status.FAILED
            # break

    # ### Migrate Apps
    # if job.stage == 'apps':
        
    #     _log("Executing App Migration...")
    #     async for result in msapp.process_job(job):
    #         _log(job.apps_type + " | " + result)
        
    #     _log("Migration of Apps is Complete.")
    #     _log(f"Execution status: {job.status}")
        
    #     if job.status == Status.COMPLETED:
    #         job.stage = 'post_apps'
            
    #     # Update
    #     save_execution(job)


async def migrate_apps_to_tenant(job: MigrationJob, dest_tenant: Tenant):
    """
    Migrate apps to a destination tenant.
        ## loop apps and validate
        ### check if app exists
        ### create app
        ### populate metadata
        ### check for errors
        ### post-process app
        ### check for errors
        ## end loop
    """
    apps = job.apps
    
    async for app in mu.validate_apps(apps, AppsType.applications):
        try:
            app: ApplicationModel = mu.prepare_app(app, job)
            existing_app: ApplicationModel = mu.get_existing_app(app, dest_tenant, job)
            # endpoint = f"{dest_tenant.endpoint}/applications"
            
            # Create app
            if not existing_app:
                # Create app
                yield f"Creating New app '{app.displayName}' on {dest_tenant.name}"
                existing_app: ApplicationModel = await mu.create_app(app, dest_tenant, job)
                # Update job
                update_migration_object(job)
            
            # Populate metadata
            if existing_app:
                yield f"Updating metadata for app '{app.displayName}' on {dest_tenant.name}"
                # existing_app: ApplicationModel = await update_app(existing_app, dest_tenant, job)
                async for res in mu.update_app(existing_app, dest_tenant, job):
                    if type(res) == str:
                        yield res
                    else:
                        existing_app = res

                update_migration_object(job)
            
            # Post-process app
            if existing_app:
                yield f"Post-processing app '{app.displayName}' on {dest_tenant.name}"
                
            # DEBUG
            print("DEBUG: Check reference Job Log file", job.log)
                
            await asyncio.sleep(1)
        
        except Exception as e:
            yield f"❌ 502 Failed to migrate app '{app.displayName}' to {dest_tenant.name}: {e}"
            # TODO add to error log
            
            await asyncio.sleep(0.1)
            continue    
    
    # yield f"Migrating '{len(apps)}' '{job.apps_type}' to '{dest_tenant.name}'"
    await asyncio.sleep(1)
    
    

async def migrate_sp_to_tenant(job: MigrationJob, dest_tenant: Tenant):
    """
    Migrate service principals to a destination tenant.
        ## loop SPs and validate
        ### check if SP exists
        ### create SP
        ### populate metadata
        ### check for errors
        ### post-process SP
        ### check for errors
        ## end loop
    """
    apps = job.service_principals
    yield f"Migrating '{len(apps)}' '{job.apps_type}' to '{dest_tenant.name}'"
    await asyncio.sleep(1)


