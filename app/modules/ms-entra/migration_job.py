# NOTE Simplify the creation of pages for admin_panel hooks
# from core.modules.admin_panel import AdminPanel, ui
# @AdminPanel.page('/{id}', title='Migration Job', viewport='full', ...) # kwargs for @router.page
# Then we skip the need to import the router and get_theme() in each module. Nor do we need the Theme.frame() wrapper.
# Theme is accessible and can use: "with AdminPanel.theme.content()" for example. 
from typing import Dict
import asyncio 

from core.modules.admin_panel import AdminPanel, ui, UIAPIRouter
from core.utils.database import Database, ObjectId
from core.common import log, print

from core.utils.string import to_snake_case
from core.utils.frontend import ui_helper
from core.utils.frontend.form_builder import FormBuilder
from core.utils.datetime import nice_time
from .src import utils, msapp
from .schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions

from .src.migration import update_migration_job

from .src.migrate_tab_edit import migrate_tab_edit
from .src.migration_tab_execute import migration_tab_execute
from .src.utils import server_request

router = UIAPIRouter()

@AdminPanel.page('/{id}', title='Migration Job', viewport='full') # kwargs for @router.page
def migration_job_edit(id:str, tab:str = 'overview'):
    """
    Main endpoint for the Migration Job Edit page
    Used to edit the job details, apps and configuration, as well as approve and execute the migration job.
    
    Workflow:
    0. Create New Migration Job, redirects to this page
    1. Job Overview (includes report and diffs, and remove apps button on dest tenants)
    2. Migration Options
    3a. Search Criteria
        3b. Select Apps
    4. Review Apps
    6. Approve App Migration
    7. Execute App Migration
        8. Review ServicePrincipal Migration (can edit)
        9. Execute ServicePrincipal Migration
    10. Final Report
    
    Tabs:
    - Overview  (includes report and diffs, and remove apps button on dest tenants)
    - Edit
        - Search
        - Select
        - Review
        - Options
        
    - Approve
    - Execute
        - Review App Migration
        - Execute App Migration
        - Review ServicePrincipal Migration
        - Execute ServicePrincipal Migration
    - Report
    - Logs
    
    
    """
    if not id:
        return ui.label("No ID provided!")

    def _tabs():
        pass
    
    with ui.tabs().classes() as tabs:
        # list = ui.tab('List')
        overview = ui.tab('Overview')
        edit = ui.tab('Edit')
        approve = ui.tab('Approve')
        execute = ui.tab('Execute')
        report = ui.tab('Report')
        logs = ui.tab('Logs')
        
    
    selected_tab = locals()[tab] if tab and tab in locals() else edit
    
    # Set up DB client
    db_client = Database.get_collection(MigrationJob.Settings.name)
    
    # get the migration_job
    migration_job = db_client.find_one({'_id': ObjectId(id)})
    migration_job = MigrationJob(**migration_job)
    
    log.debug(str(migration_job)[:500] + "...")
    
    # fallback  # TODO Should be a dict, not a list!!
    if isinstance(migration_job.source_tenant, list):
        log.error("Source Tenant is a list! Should be a dict")
        # migration_job.source_tenant = migration_job.source_tenant[0]
        source_tenant = migration_job.source_tenant[0]
    else:
        source_tenant = migration_job.source_tenant

    # source_tenant = migration_job.source_tenant.name
    
    # Pagination

        
    async def _approve_job() -> None:
        
        async def _approve_migration_job() -> None:
            migration_job.status = Status.APPROVED
            migration_job.stage = "apps"
            # TODO add approved_by parameters
            # migration_job.approved_by = get_user()
            # migration_job.approved_at = datetime.now()
            
            try:
                await update_migration_job(migration_job.id, migration_job.model_dump())
                ui.notify("Migration Job Approved!", type='positive')
                await asyncio.sleep(1)
                dialog2.close()
                ui.navigate.to(f"/ms-entra/migrate-job/{migration_job.id}?tab=execute")
            except Exception as e:
                log.error(e)
                ui.notify(f"Failed to approve Migration Job: {e}", type='negative')
                await asyncio.sleep(3)
                dialog2.close()
            
        with ui.dialog() as dialog2, ui.card():
            ui.label('Are you sure you want to Approve this Job?')
            if migration_job.status != Status.PENDING_APPROVAL:
                ui_helper.alert_warning("Job can only be Approved if the status is PENDING_APPROVAL.")
                
            with ui.row():
                if migration_job.status == Status.PENDING_APPROVAL:
                    ui.button('Confirm',icon="check", on_click=_approve_migration_job ).props('positive').classes('bg-positive text-white')
                ui.button('Cancel', on_click=dialog2.close).props("primary")
        
        dialog2.open()
              
    # Display the page
    # def display_page():
    with ui.tab_panels(tabs, value=selected_tab).props('q-pa-none').classes('full-width').style("background: none;"):
        
        with ui.tab_panel(overview).props('q-pa-none'):
            with AdminPanel.theme().content("Overview"):
                # TODO Make it in a table.
                ui.label(f"Job Name: {migration_job.name}")
                ui.label(f"Status: {migration_job.status}")
                ui.label(f"Stage: {migration_job.stage.capitalize()}")
                ui.label(f"Source Tenant: {source_tenant.name}")
                ui.label(f"Destination Tenants: {', '.join([t.name for t in migration_job.destination_tenants])}")
                ui.label("Migration Options")
                ui.json_editor({'content':{'json': migration_job.migration_options.model_dump()}})
                ui.separator()
                ui.label(f"Apps to Migrate: {len(migration_job.apps)}")
                ui.label(f"Apps Type: {migration_job.apps_type}")
                ui.separator() 
        
        
        with ui.tab_panel(edit).props('q-pa-none'):
            with AdminPanel.theme().content("Edit"):
                migrate_tab_edit(migration_job, source_tenant)
            
                
        with ui.tab_panel(approve).props('q-pa-none'):
            with AdminPanel.theme().content("Migration Approval"):
                
                ui.label("Migration Summary").classes('font-bold text-lg')
                ui.separator()
                ui.label(f"Migration Job: {migration_job.name}")
                ui.label(f"Status: {migration_job.status}")
                ui.label(f"Stage: {migration_job.stage.capitalize()}")
                # 1. Check status is correct
                if migration_job.status != Status.PENDING_APPROVAL:
                    ui_helper.alert_error(f"Migration Job is not in PENDING_APPROVAL status. Current status: {migration_job.status}")
                ui.label(f"Source Tenant: {source_tenant.name}")
                ui.label(f"Destination Tenants: {', '.join([t.name for t in migration_job.destination_tenants])}")
                ui.label("Migration Options")
                ui.json_editor({'content':{'json': migration_job.migration_options.model_dump()}})
                ui.separator()
                ui.label(f"Apps to Migrate: {len(migration_job.apps)}")
                ui.label(f"Apps Type: {migration_job.apps_type}")
                ui.label("Apps")
                ui.json_editor({'content':{'json': migration_job.apps}})
                ui.separator() 
                
                if migration_job.status == Status.PENDING_APPROVAL:
                    ui.button("Approve Migration Job", on_click=_approve_job).classes("bg-positive text-white")
                
        
        with ui.tab_panel(execute).props('q-pa-none'):
            with AdminPanel.theme().content("Migration Execution"):
                migration_tab_execute(migration_job, source_tenant)
                
        with ui.tab_panel(report).props('q-pa-none'):
            with AdminPanel.theme().content("Overview"):
                
                def _del_button_apps():
                    _delete_apps('applications')
                def _del_button_sp():
                    _delete_apps('servicePrincipals')
                def _delete_apps(type):
                    """
                    Delete the apps from the destination tenants
                    """
                    ui.notify(f"Deleting {type} from Destination Tenants")
                    for dest_tenant in migration_job.destination_tenants:

                        try:
                            
                            _dest_tenant:Tenant = msapp.connect_tenant(dest_tenant.model_dump())
                                        
                            if not _dest_tenant.access_token:
                                raise 
                            
                            dest_tenant.access_token = _dest_tenant.access_token
                            
                        except Exception as e:
                            log.error(e)
                            raise Exception(f"Failed to connect to destination tenant: {dest_tenant.name}")
                        
                        endpoint = dest_tenant.endpoint
                        apps = migration_job.app_id_mapping if type == 'applications' else migration_job.sp_id_mapping
                        for k,v in apps.items():
                            if v.get(dest_tenant.client_id):
                                app_id = v[dest_tenant.client_id].get('appId')
                                ui.notify(f"Deleting {type} from {dest_tenant.name}")
                                # TODO delete apps
                                try:
                                    endpoint += f"/{type}(appId='{app_id}')"
                                    req = server_request(
                                        endpoint, 
                                        method="DELETE", 
                                        api_key=dest_tenant.access_token, 
                                        # host=dest_tenant.endpoint
                                    )
                                
                                    if req and req.status_code == 204:
                                        ui.notify(f"✅ Deleted {type}:{app_id} from {dest_tenant.name}")
                                    else:
                                        log.error(req.text)
                                        ui.notify(f"❌ Failed to delete {type}:{app_id} from {dest_tenant.name}: {req.text}", type='negative')

                                except Exception as e:
                                    log.error(e)
                                    ui.notify(f"Failed to delete {type} from {dest_tenant.name}", type='negative')
                                # msapp.delete_apps(dest_tenant, migration_job.apps)
                
                ui.label("Apps Migrated")
                ui.json_editor({'content':{'json': migration_job.app_id_mapping}})
                ui.label("Service Principals Migrated")
                ui.json_editor({'content':{'json': migration_job.sp_id_mapping}})
                ui.label("Format")
                ui.codemirror("{\n 'source AppId': {\n  'destination Tenant Client Id': { \n    'appId': 'new AppId on destination Tenant', \n    'data': 'new App manifest' \n  }\n }\n}", language='json').classes()
                ui.label("Apps Failed")
                ui.json_editor({'content':{'json': migration_job.apps_failed}})
                ui.label("App Migration Diff")
                ui.json_editor({'content':{'json': migration_job.app_diff()}})
                ui.button("Delete Apps", on_click=_del_button_apps ).classes("bg-negative text-white")
                ui.label("Service Principal Migration Diff")
                ui.json_editor({'content':{'json': migration_job.sp_diff()}})
                ui.button("Delete Service Principals", on_click=_del_button_sp ).classes("bg-negative text-white")
            
        with ui.tab_panel(logs).props('q-pa-none'):
            with AdminPanel.theme().content("Logs"):
                ui.label("Migration Execution Log")
                ui.separator()
                output_log = ui.log().classes('w-full full-width h-300')                
                
                if migration_job.log:
                    for l in migration_job.log:
                        output_log.push(l)
