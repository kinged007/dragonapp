# NOTE Simplify the creation of pages for admin_panel hooks
# from core.modules.admin_panel import AdminPanel, ui
# @AdminPanel.page('/{id}', title='Migration Job', viewport='full', ...) # kwargs for @router.page
# Then we skip the need to import the router and get_theme() in each module. Nor do we need the Theme.frame() wrapper.
# Theme is accessible and can use: "with AdminPanel.theme.content()" for example. 
from typing import Dict
import asyncio 

from core.modules.admin_panel import AdminPanel, ui, APIRouter
from core.utils.database import Database, ObjectId
from core.common import log, print

from core.utils.string import to_snake_case
from core.utils.frontend import ui_helper
from core.utils.frontend.form_builder import FormBuilder
from core.utils.datetime import nice_time
from .src import utils, msapp
from .schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions

from .src.migration import update_migration_job

router = APIRouter()

@AdminPanel.page('/{id}', title='Migration Job', viewport='full') # kwargs for @router.page
def migration_job_edit(id:str, tab:str = 'edit'):
    
    if not id:
        return ui.label("No ID provided!")

    def _tabs():
        pass
    
    with ui.tabs().classes() as tabs:
        # list = ui.tab('List')
        edit = ui.tab('Edit')
        approve = ui.tab('Approve')
        execute = ui.tab('Execute')
    
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
    
    
    list_of_apps = []
    
    def perform_search(event):
        
        nonlocal list_of_apps
        
        if not migration_job:
            ui.notification("Migration Job DB Item could not be found!", type='negative')
            return 
        
        if not source_tenant:
            ui.notification("Source Tenant not found!", type='negative')
            return
                
        # Prepare tenant object
        tenant = msapp.connect_tenant(source_tenant.model_dump())
        
        if not tenant or not tenant.access_token:
            ui.notification("Failed to connect to the source tenant!", type='negative')
            return
        
        # Fetch listing
        try:
            list_of_apps = msapp.fetch_listing(migration_job.apps_type, endpoint=f"/{migration_job.apps_type}", tenant=tenant, query={
                "search": _search.value, 
                "filter": _filter.value, 
                "raw_params": _raw.value, 
                "skip_publishers": _skip_publishers.value if _skip_publishers else None, 
            })
        except Exception as e:
            ui.notification(f"Failed to fetch listing: {e}", type='negative', close_button=True)
            return
        
        if list_of_apps:
            ui.notification(f"Found {len(list_of_apps)} apps!", type='positive')
        
        # print(apps)
        # print(_search.value)
        # print(_filter.value)
        # print(_raw.value)
        # print(_skip_publishers.value if _skip_publishers else None)
        
        # _json_editor_results.properties={'content': {'json': apps}}
        # ui_helper.table([
        #     {"id":123, "name":"App 1", "publisher":"Microsoft"},
        #     {"id":124, "name":"App 2", "publisher":"Microsoft"},
        #     {"id":125, "name":"App 3", "publisher":"Microsoft"},
        #     {"id":126, "name":"App 4", "publisher":"Microsoft"},
        # ], row_key='id', title="Search Results")
        # table_of_results.clear()
        # table_of_results.remove_rows(table_of_results.selected)
        table_of_results.rows = []
        # table_of_results.add_rows(apps)
        # columns = []
        # for k,v in apps[0].items():
        #     if type(v) not in [str]: continue
        #     columns.append({
        #         "name": k,
        #         "label": k,
        #         "field": k,
        #         "sortable": True,
        #         "align": "left" if type(v) in [str, int, float] else "right",
        #         "classes": "hidden",
        #         "headerClass": "hidden"
        #         })
        #     if len(columns) > 5: break
        # table_of_results.columns = columns
        for r in [{k:str(v) for k,v in a.items()} for a in list_of_apps]:
            table_of_results.add_rows(r)
        table_of_results.update()
        table_of_results.run_method('scrollTo', len(table_of_results.rows)-1)

        _update_json_editor()
        
        stepper.next()

        # _json_editor_results.run_editor_method('updateProps', {'content': {'json': apps}})
    
    search_templates = []
    search_templates_display = []
    
    def fetch_search_templates(type='applications'):
        """
        Fetch search templates from the DB
        """
        nonlocal search_templates, search_templates_display
        db_client = Database.get_collection('ms_entra_migration_search_templates')
        items = db_client.find({'app_type': type }).sort('name', 1)
        if not items: return []
        search_templates = list(items)
        search_templates_display =  [i.get('name') for i in list(items)]
        
    def apply_search_template(template=None):
        nonlocal search_templates
        _options = [i for i in search_templates if i.get('name') == template ]
        if not _options:
            ui.notification("Template not found!", type='negative')
            return
        log.debug("Applying search template: " + str(_options[0]))
        _template = _options[0]
        
        _search.value = _template.get('field_search', "")
        _filter.value = _template.get('field_filter', "")
        _raw.value = _template.get('field_raw', "")
        if _skip_publishers:
            _skip_publishers.value = _template.get('field_skip_publishers', [])
    
    def save_search_template():
        
        # Save search template
        def _save_template():
            db_client = Database.get_collection('ms_entra_migration_search_templates')
            _template = SearchTemplates(**{
                "app_type": migration_job.apps_type.value,
                "name": _template_name.value,
                "field_search": _search.value,
                "field_filter": _filter.value,
                "field_raw": _raw.value,
                "field_skip_publishers": _skip_publishers.value if _skip_publishers else [],
            })
            db_client.insert_one(_template.model_dump())
            ui.notification("Search Template Saved!", type='positive')
            dialog.close()
            search_templates_display.append(_template_name.value)
            search_box.refresh() # Update search box
        
        # Popup for name input
        with ui.dialog().classes("full-width q-pa-lg col-12") as dialog, ui.card():
            with ui.row():
                _template_name = ui.input("Template Name", placeholder="Enter a name for the template").classes("full-width")
                ui.button("Save", on_click= _save_template ).classes("bg-positive text-white")
                ui.button("Cancel", on_click=dialog.close).classes("bg-primary text-white")
        dialog.open()
        
    def _update_json_editor(event=None):
        nonlocal list_of_apps
        _ids = [r.get('id') for r in table_of_results.selected]
        _json_editor_results.run_editor_method('updateProps', {'content': {'json': [l for l in list_of_apps if l.get('id') in _ids]}}, timeout=10)
        # _json_editor_results.update() # BUG with this, output is table_of_results.selected (strings) -1, without it, output is empty the first time, then second time is list_of_apps (dicts) +1
        stepper.next()
        stepper.previous()
        stepper.next()
        # _json_editor_results.run_editor_method('updateProps', {'content': {'json': [l for l in list_of_apps if l.get('id') in _ids]}})
        
    async def _confirm_submit_json_data() -> None:
        
        async def _update_migration_job() -> None:
            data = await _json_editor_results.run_editor_method('get')
            data = data.get('json',[])
            if not data or len(data) == 0:
                ui.notify("No data selected!")
                return
            
            
            migration_job.apps = data
            migration_job.status = Status.PENDING_APPROVAL
            migration_job.search_params = {
                "search": _search.value,
                "filter": _filter.value,
                "raw": _raw.value,
                "skip_publishers": _skip_publishers.value if _skip_publishers else [],
            }
            migration_job.migration_options = MigrationOptions(**form_migration_options.current_values)
            
            # Update
            try:
                await update_migration_job(migration_job.model_dump())
                ui.notify("Migration Job Updated!", type='positive')
                print("SAVE MIGRATION JOB GOOD", migration_job)
                dialog.close()
                
                ui.navigate.to(f"/ms-entra/migrate-job/{migration_job.id}?tab=approve")
                
            except Exception as e:
                log.error(e)
                ui.notify(f"Failed to update Migration Job: {e}", type='negative')
                print("SAVE MIGRATION JOB FAIL", migration_job)
                dialog.close()
                
            # # res = db_client.update_one({'_id': ObjectId(id) }, {"$set": {"apps": data, "status": Status.PENDING_APPROVAL.value }})
            # res = db_client.update_one({'_id': ObjectId(id) }, {"$set": migration_job.model_dump(exclude=['destination_tenants','source_tenant']) })
            # ui.notify("Migration Job Updated!", type='positive')
            # print("SAVE MIGRATION JOB", data)
            # dialog.close()
            
        data = await _json_editor_results.run_editor_method('get')

        if not data.get("json",None) or len(data.get("json",[])) == 0:
            ui.notify("No data selected!")
            return
        
        with ui.dialog() as dialog, ui.card():
            ui.label('Are you sure you want to migrate these apps?')
            if migration_job.status == Status.APPROVED or migration_job.status == Status.COMPLETED:
                ui_helper.alert_warning(f"This JOB can not be modified. Current Status: {migration_job.status}")
                
            with ui.row():
                if migration_job.status != Status.APPROVED and migration_job.status != Status.COMPLETED:
                    ui.button('Confirm',icon="check", on_click=_update_migration_job ).props('positive').classes('bg-positive text-white')
                ui.button('Cancel', on_click=dialog.close).props("primary")
        
        dialog.open()
        
    async def _approve_job() -> None:
        
        async def _approve_migration_job() -> None:
            migration_job.status = Status.APPROVED
            # TODO add approved_by parameters
            # migration_job.approved_by = get_user()
            # migration_job.approved_at = datetime.now()
            
            try:
                await update_migration_job(migration_job.model_dump())
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
        
        
        with ui.tab_panel(edit).props('q-pa-none'):
            # with AdminPanel.theme().content("Apps Search"):
        
            if migration_job.status == Status.APPROVED or migration_job.status == Status.COMPLETED:
                ui_helper.alert_warning(f"This JOB can not be modified. Current Status: {migration_job.status}")
            
            with ui.column():
            
                with ui.stepper().props().classes('w-full full-width') as stepper:
                    
                    with ui.step('Search Criteria'):

                        app_type = migration_job.apps_type
                                                
                        ui.label(f"Searching '{app_type}' from Tenant '{source_tenant.name}'").classes('font-bold text-lg')
                        
                        # Fetch search templates
                        fetch_search_templates(app_type)
                        
                        # ## DEBUG TEST
                        # Database Ref box
                        # _dbref_options = list(Database.get_collection('ms_entra_tenants').find({}))
                        # print(_dbref_options)
                        # ui.label("Database Ref Test").classes('font-bold text-lg')
                        # @ui.refreshable
                        # def _test_ref():
                        #     with ui.row().classes('full-width') as row:
                        #         _search = ui.select(
                        #             options = [s.get('name') for s in _dbref_options], # Use display_field template
                        #             label = "DB REF",
                        #             multiple=True, # If LIST
                        #             with_input = True, #	whether to allow new values
                        #             on_change=lambda: ui.notification([v for v in _dbref_options if v.get('name') == _search.value]),
                        #             # new_value_mode="add",
                        #             clearable=True, # If Optional
                        #         ).classes('col-12').props('use-chips')
                        #         ui.button("Go", on_click=lambda: ui.notify([v for v in _dbref_options if v.get('name') == _search.value])).classes('bg-positive text-white')
                        # _test_ref()
                        ## DEBUG END
                        
                        
                        # Search box
                        @ui.refreshable
                        def search_box():

                            with ui.row().classes('full-width') as row:
                                _search = ui.select(
                                    options = search_templates_display,
                                    label = "Search Template",
                                    with_input = True, #	whether to allow new values
                                ).classes('col-10').props()
                                ui.button('Apply', on_click=lambda: apply_search_template( _search.value)).classes('bg-positive text-white')
                                
                        search_box()
                        
                        
                        
                        # Search fields
                        with ui.row().classes("full-width") as row:
                            ui_helper.alert_info("Search & Filter Fields. See https://learn.microsoft.com/en-us/graph/search-query-parameter for more information on search/filter.")
                            # ui.label("Search & Filter Fields. See ()[https://learn.microsoft.com/en-us/graph/search-query-parameter] for more information on search/filter.").classes('bordered text-caption')
                            _search = ui.input("Search Field", placeholder="displayName:appname").classes("full-width")
                            _filter = ui.input("Filter Field", placeholder="").classes("full-width")
                            _raw = ui.input("RAW URL Parameters", placeholder="$top=10").classes("full-width")
                            if app_type == "servicePrincipals":
                                _skip_publishers = ui.select(label="Skip Publishers", options=[
                                    "Microsoft Services",
                                    "Microsoft Accounts",
                                    "Microsoft 365 PnP",
                                    "Microsoft 365",
                                    "Microsoft Azure",
                                    "Microsoft",
                                    "graphExplorerMT",
                                    "Citrix Cloud",
                                ], 
                                    multiple=True, 
                                    clearable=True,
                                    with_input=True,
                                    new_value_mode="add",
                                ).classes("full-width").props('use-chips')
                            else:
                                _skip_publishers = None
                            
                            # Update fields with existing values
                            if migration_job.search_params:
                                _search.value = migration_job.search_params.get('search', "")
                                _filter.value = migration_job.search_params.get('filter', "")
                                _raw.value = migration_job.search_params.get('raw', "")
                                if _skip_publishers:
                                    _skip_publishers.value = migration_job.search_params.get('skip_publishers', [])
                            
                        with ui.stepper_navigation():
                            ui.button("Search", on_click=perform_search).classes("bg-positive text-white")
                            ui.button("Save Search", on_click= save_search_template ).classes("bg-primary text-white")

                        # Fetch Apps
                    with ui.step("Select Apps").classes('full-width col-12'):
                        # Table view
                        table_of_results = ui_helper.table([], columns=[
                            {"name": "id", "label": "ID", "field": "id", "sortable": True, "align": "left", "classes": "hidden", "headerClass": "hidden"},
                            {"name": "appId", "label": "appId", "field": "appId", "sortable": True, "align": "left", "classes": "", "headerClass": ""},
                            {"name": "displayName", "label": "displayName", "field": "displayName", "sortable": True, "align": "left", "classes": "", "headerClass": ""},
                                
                        ], row_key='id', title="Search Results", selection='multiple', pagination=50
                        # columns=columns,
                        ).classes('full-width col-12')
                        
                        # Add JSON Viewer dialog # DEPRECATE
                        # with ui.dialog().classes("full-width q-pa-lg col-12") as dialog, ui.card().classes("full-width"):
                        #     _quick_json_view = ui.json_editor({'content': {'json': []}})
                        
                        # Add buttons
                        with table_of_results.add_slot('top-right'):
                            # ui.button("View JSON", icon="visibility", on_click=_view_json).classes("bg-positive text-white")
                            ui_helper.table_buttons(table_of_results, ['json', 'fullscreen','columns'], real_rows=lambda: list_of_apps)
                        
                        # Add selected items
                        table_of_results.selected = migration_job.apps or []
                        
                        with ui.stepper_navigation():

                            ui.button("Review Selected Apps", on_click= _update_json_editor ).classes("bg-positive text-white")
                            ui.button('Back', on_click=stepper.previous).props('flat')

                        
                    with ui.step("Review Apps").classes('col-12 full-width'):
                        
                        # _ids = [r.get('id') for r in table_of_results.selected]
                        # _data = [l for l in list_of_apps if l.get('id') in _ids]
                        _json_editor_results = ui.json_editor({'content': {'json': table_of_results.selected}})
                        
                        # TEMP
                        ui_helper.alert_info("If apps are not showing in JSON editor, go back then forward to refresh the data.")
                        
                        with ui.stepper_navigation():

                            ui.button('Submit Apps', on_click= stepper.next ).classes("bg-positive text-white")
                            ui.button('Back', on_click=stepper.previous).props('flat')

                    #   Review Migration Options
                    with ui.step("Migration Options").classes('col-12 full-width'):
                        
                        # ui.label("Migration Options").classes('font-bold text-lg')
                        _schema = MigrationOptions.model_json_schema()
                        # print(_schema)
                        # print("PARSED SCHEMA", ui_helper.json_schema_parser(_schema))
                        form_migration_options = FormBuilder(_schema, migration_job.migration_options.model_dump() )
                        form_migration_options.submit_value = None
                        form_migration_options.build_main_form()
                        
                        with ui.stepper_navigation():

                            ui.button('Save Migration Job', on_click=_confirm_submit_json_data ).classes("bg-positive text-white")
                            ui.button('Back', on_click=stepper.previous).props('flat')
                    
            
            
            # with AdminPanel.theme().content("Apps Explorer"):
            # with ui.column().classes('full-width'):
                # ui.label("Search Results").classes('font-bold text-lg')
                
                

                
        with ui.tab_panel(approve).props('q-pa-none'):
            with AdminPanel.theme().content("Migration Approval"):
                
                

                ui.label("Migration Summary").classes('font-bold text-lg')
                ui.separator()
                ui.label(f"Migration Job: {migration_job.name}")
                ui.label(f"Status: {migration_job.status}")
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
                
                # Migration callback
                async def _process_migration():
                    n = ui.notification(timeout=None)
                    try:
                        data = await migration_options.run_editor_method('get')
                        await asyncio.sleep(0.1)
                        migration_job_execution.migration_options = MigrationOptions(**data.get('json',{})) 
                        
                        n.spinner = True
                        output_log.push(f"{nice_time()} | Executing Migration...")
                        migration_job_execution.log.append(f"{nice_time()} | Executing Migration....")
                        await asyncio.sleep(1)
                        
                        async for result in msapp.process_migration_job(migration_job_execution):
                            output_log.push(f"{nice_time()} | {result}.")
                            migration_job_execution.log.append(f"{nice_time()} | {result}.")
                        
                        n.message = "Migration Job Executed"
                        n.icon = 'check'
                        n.spinner = False
                        n.type = 'positive'
                        await asyncio.sleep(1)
                        n.dismiss()
                        if migration_job_execution.status == Status.COMPLETED:
                            ui.notify("Migration Job Completed", type='positive')
                            execute_button.disable()
                        # ui.notify("Migration Job Executed", type='positive')
                        # Job is saved in  the execution method
                        
                    except Exception as e:
                        output_log.push(f"{nice_time()} | Error: {e}")
                        migration_job_execution.log.append(f"{nice_time()} | Error: {e}.")
                        n.dismiss()
                        ui.notify(f"Error: {e}", type='negative')                
                
                # Re-fetch the migration job
                
                # get the migration_job
                migration_job_execution = db_client.find_one({'_id': ObjectId(migration_job.id)})
                migration_job_execution = MigrationJob(**migration_job_execution)
                _ready = True
                
                # Process
                # 1. Check status is correct
                if migration_job_execution.status != Status.APPROVED:
                    ui_helper.alert_error(f"Migration Job is not in APPROVED status. Current status: {migration_job_execution.status}")
                    _ready = False
                
                # 2. Check source_tenant exists and destination tenants exist
                if not migration_job_execution.source_tenant:
                    ui_helper.alert_error(f"Source Tenant not set.")
                    _ready = False
                    
                if not migration_job_execution.destination_tenants:
                    ui_helper.alert_error(f"Destination Tenants not set.")
                    _ready = False
                
                # 3. Check apps to migrate
                if not migration_job_execution.apps:
                    ui_helper.alert_error(f"No Apps to migrate.")
                    _ready = False

                if _ready:
                    
                    # fallback  # TODO Should be a dict, not a list!!
                    if isinstance(migration_job_execution.source_tenant, list):
                        log.error("Source Tenant is a list! Should be a dict")
                        migration_job_execution.source_tenant = migration_job.source_tenant[0]
                    
                    ui.label("Migration Summary").classes('font-bold text-lg')
                    ui.separator()
                    ui.label(f"Migration Job: {migration_job_execution.name}")
                    ui.label(f"Status: {migration_job_execution.status}")
                    ui.label(f"Approved by: TODO")
                    ui.label(f"Approved on: TODO")
                    ui.separator()
                    ui.label(f"Source Tenant: {migration_job_execution.name}")
                    ui.label(f"Destination Tenants: {', '.join([t.name for t in migration_job_execution.destination_tenants])}")
                    ui.label("Migration Options")
                    migration_options = ui.json_editor({'content':{'json': migration_job_execution.migration_options.model_dump()}})
                    ui.separator()
                    ui.label(f"Apps to Migrate: {len(migration_job_execution.apps)}")
                    ui.label(f"Apps Type: {migration_job_execution.apps_type}")
                    ui.separator() 
                    
                    with ui.row():
                        execute_button = ui.button("Execute Migration", on_click=_process_migration ).classes("bg-positive text-white")
                        ui.button("Execute Post-Processing Migration" )
                        ui.button("View Report" )
                    
                ui.label("Migration Execution Log")
                ui.separator()
                output_log = ui.log().classes('w-full h-100')                
                
                if migration_job_execution.log:
                    for l in migration_job_execution.log:
                        output_log.push(l)
                