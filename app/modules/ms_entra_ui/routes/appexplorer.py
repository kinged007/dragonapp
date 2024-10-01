from nicegui import ui
import asyncio, json
from core.utils.frontend import ui_helper, ui, FormBuilder
from core.utils.database import Database
from core import log, print
from app.modules.ms_entra.schema import Tenant, Status, MigrationJob, MigrationOptions
from app.modules.ms_entra.src import utils, msapp
from app.modules.ms_entra.schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions
from app.modules.ms_entra.src.migration import update_migration_job
from app.modules.ms_entra.schema import Tenant, MigrationJob, Status, AppsType
from app.modules.ms_entra.models.applications import ApplicationModel, passwordCredentialResource, keyCredentialResource
from app.modules.ms_entra.models.service_principals import ServicePrincipalModel


async def app_explorer():
    ui.label("App Explorer!!!")

    list_of_apps = []
    source_tenant = None
    source_tenant_name = source_tenant.name if source_tenant else "No Tenant Selected"
    
    with ui.column():

        with ui.stepper().props().classes('w-full full-width') as stepper:
            
            async def _update_json_editor():
                nonlocal list_of_apps
                                    
                stepper.next()
                
                
                if list_of_apps:
                    if callable(list_of_apps):
                        _rows = list_of_apps()
                    else:
                        _rows = list_of_apps
                    _selected_rows = [r.get(table_of_results.row_key) for r in table_of_results.selected]
                    _json = [l for l in _rows if l.get(table_of_results.row_key) in _selected_rows]
                else:
                    _json = table_of_results.selected
                # __json_viewer.run_editor_method('updateProps', {'content': {'json': _json}})
                # dialo_json_viewer.open()
                #     __json_viewer = ui.json_editor({'content': {'json': []}}).props('full-width')
                # d = _json_editor_results.run_editor_method('updateProps', {'content': {'json': _json }}, timeout=10)
                _json_applications.run_editor_method( 'update', {'json': _json } )
                
                
                if _fetch_service_principals.value == True and _json:
                    ui.notify("Fetching Service Principals")
                    _app_ids = [r.get('appId') for r in _json]
                    _sps = await msapp.fetch_sp_from_apps(_app_ids, source_tenant)
                    _json_service_principals.run_editor_method( 'update', {'json': _sps } )
                    print("ServicePrincipals", str(_sps)[:300])

                # with ui.dialog() as dialo_json_viewer:
                print("Applications", str(_json)[:300])
                

                                

                
                # _ids = [r.get('id') for r in table_of_results.selected]
                # _json_editor_results.run_editor_method('updateProps', {'content': {'json': [l for l in list_of_apps if l.get('id') in _ids]}}, timeout=10)
                # # _json_editor_results.update() # BUG with this, output is table_of_results.selected (strings) -1, without it, output is empty the first time, then second time is list_of_apps (dicts) +1
                # # _json_editor_results.set({'content': {'json': [l for l in list_of_apps if l.get('id') in _ids]}}) 
                # stepper.next()
                # stepper.previous()
                # _json_editor_results.run_editor_method('updateProps', {'content': {'json': [l for l in list_of_apps if l.get('id') in _ids]}})

            
            
            with ui.step('Search Criteria'):

                def perform_search(event):
                    
                    nonlocal list_of_apps, source_tenant
                    
                    # if not migration_job:
                    #     ui.notification("Migration Job DB Item could not be found!", type='negative')
                    #     return 
                    
                    if _tenant and _tenant.value:
                        source_tenant = [t for t in tenants_list if t.get('name') == _tenant.value]
                        if source_tenant: source_tenant = Tenant(**source_tenant[0])
                        
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
                        # list_of_apps = msapp.fetch_listing(migration_job.apps_type, endpoint=f"/{migration_job.apps_type}", tenant=tenant, query={
                        list_of_apps = msapp.fetch_listing(_app_type.value, endpoint=f"/{_app_type.value}", tenant=tenant, query={
                            "search": _search.value, 
                            "filter": _filter.value, 
                            "raw_params": _raw.value, 
                            "skip_publishers": _skip_publishers.value if _skip_publishers and _app_type.value == 'servicePrincipals' else None, 
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

                    # _update_json_editor()
                    
                    stepper.next()

                    # _json_editor_results.run_editor_method('updateProps', {'content': {'json': apps}})
                
                search_templates = []
                search_templates_display = []
                tenants_list = []
                tenants_list_display = []
                
                def fetch_tenant_list():
                    """
                    Fetch tenants from the DB
                    """
                    nonlocal tenants_list, tenants_list_display
                    db_client = Database.get_collection(Tenant.Settings.name)
                    items = db_client.find().sort('name', 1)
                    if not items: return []
                    tenants_list = list(items)
                    tenants_list_display =  [i.get('name') for i in list(items)]
                    
                def fetch_search_templates(type='applications'):
                    """
                    Fetch search templates from the DB
                    """
                    nonlocal search_templates, search_templates_display
                    db_client = Database.get_collection(SearchTemplates.Settings.name)
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
                            "app_type": 'applications',
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
                
                
                # Fetch tenants
                fetch_tenant_list()
                
                with ui.row().classes('full-width') as row:
                    _tenant = ui.select(
                        options = tenants_list_display,
                        label = "Select Tenant",
                        with_input = True, #	whether to allow new values
                    ).classes('col-10').props()
                    ui.button('Confirm', on_click=lambda: apply_search_template( _search.value)).classes('bg-positive text-white')

                with ui.row().classes('full-width').bind_visibility_from(_tenant, target_name='value') as row:
                    
                    ui.label(f"Selected Tenant: {source_tenant_name}").classes('font-bold text-lg').bind_text_from(_tenant, 'value', backward= lambda a: f"Searching in Tenant: {a}")
                        
                    app_type = 'applications'
                                            
                    # ui.label(f"Searching '{app_type}' from Tenant '{source_tenant_name}'").classes('font-bold text-lg')
                    ui.label(f"Search for Apps on Tenant '{source_tenant_name}'").classes('font-bold text-lg')
                    
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
                        _app_type = ui.select(label="App Type", options=['applications','servicePrincipals'], value='applications').classes("full-width")
                        _search = ui.input("Search Field", placeholder="displayName:appname").classes("full-width")
                        _filter = ui.input("Filter Field", placeholder="").classes("full-width")
                        _raw = ui.input("RAW URL Parameters", placeholder="$top=10").classes("full-width")
                        # if app_type == "servicePrincipals":
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
                        ).classes("full-width").props('use-chips').bind_visibility_from(_app_type, 'value', value='servicePrincipals')
                        # else:
                        #     _skip_publishers = None
                        
                        # Update fields with existing values
                        # if migration_job.search_params:
                        #     _search.value = migration_job.search_params.get('search', "")
                        #     _filter.value = migration_job.search_params.get('filter', "")
                        #     _raw.value = migration_job.search_params.get('raw', "")
                        #     if _skip_publishers:
                        #         _skip_publishers.value = migration_job.search_params.get('skip_publishers', [])
                        
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
                table_of_results.selected = []
                
                _fetch_service_principals = ui.switch("Fetch Service Principals", value=False).classes("")
                
                with ui.stepper_navigation():

                    # ui.button("Review Selected Apps", on_click= lambda: _update_json_editor(list_of_apps) ).classes("bg-positive text-white")
                    ui.button("Review Selected Apps", on_click= _update_json_editor ).classes("bg-positive text-white")
                    ui.button('Back', on_click=stepper.previous).props('flat')

            with ui.step("Review Apps").classes('col-12 full-width'):
                                            
                async def _confirm_submit_json_data() -> None:
                    
                    async def _update_migration_job() -> None:
                        data_applications = await _json_applications.run_editor_method('get')
                        data_service_principals = await _json_service_principals.run_editor_method('get')
                        data_applications = data_applications.get('json',[])
                        data_service_principals = data_service_principals.get('json',[])
                        if not data_applications or len(data_applications) == 0:
                            ui.notify("No data selected!")
                            return
                        
                        ui.notify(f"SAVING METADATA TO NEW MIGRATION TICKET", type='positive')
                        print("SAVE MIGRATION JOB:Apps", str(data_applications)[:200])
                        print("SAVE MIGRATION JOB:SP", str(data_service_principals)[:200])
                        
                        # Save new Ticket with app data
                        migration_job = MigrationJob(**{
                            "apps": data_applications,
                            "service_principals": data_service_principals,
                        })
                        
                        res = Database.get_collection(MigrationJob.Settings.name).insert_one(migration_job.model_dump())
                        log.debug(res)
                        
                        if res:
                            ui.notify("Migration Job Created!", type='positive')
                            ui.navigate.to(f"/ticket/view/{res.inserted_id}")
                        
                        # migration_job.apps_type = _app_type.value
                        # if migration_job.apps_type == 'servicePrincipals':
                        #     migration_job.service_principals = data
                        # else:
                        #     migration_job.apps = data
                        # migration_job.status = Status.PENDING_APPROVAL
                        # migration_job.search_params = {
                        #     "search": _search.value,
                        #     "filter": _filter.value,
                        #     "raw": _raw.value,
                        #     "skip_publishers": _skip_publishers.value if _skip_publishers and _app_type.value == 'servicePrincipals' else [],
                        # }
                        # migration_job.migration_options = MigrationOptions(**form_migration_options.current_values)
                        
                        # # Update
                        # try:
                        #     await update_migration_job(migration_job.id, migration_job.model_dump())
                        #     ui.notify("Migration Job Updated!", type='positive')
                        #     print("SAVE MIGRATION JOB GOOD", migration_job)
                        #     dialog.close()
                            
                        #     ui.navigate.to(f"/ms_entra/migrate-job/{migration_job.id}?tab=approve")
                            
                        # except Exception as e:
                        #     log.error(e)
                        #     ui.notify(f"Failed to update Migration Job: {e}", type='negative')
                        #     print("SAVE MIGRATION JOB FAIL", migration_job)
                        #     dialog.close()
                            
                        # # res = db_client.update_one({'_id': ObjectId(id) }, {"$set": {"apps": data, "status": Status.PENDING_APPROVAL.value }})
                        # res = db_client.update_one({'_id': ObjectId(id) }, {"$set": migration_job.model_dump(exclude=['destination_tenants','source_tenant']) })
                        # ui.notify("Migration Job Updated!", type='positive')
                        # print("SAVE MIGRATION JOB", data)
                        # dialog.close()
                        
                    data_applications = await _json_applications.run_editor_method('get')
                    data_service_principals = await _json_service_principals.run_editor_method('get')

                    if not data_applications.get("json",None) or len(data_applications.get("json",[])) == 0:
                        ui.notify("No data selected!")
                        return
                    
                    with ui.dialog() as dialog, ui.card():
                        ui.label('Are you sure you want to create a new ticket with this App Metadata?')
                        # if migration_job.status == Status.APPROVED or migration_job.status == Status.COMPLETED:
                        #     ui_helper.alert_warning(f"This JOB can not be modified. Current Status: {migration_job.status}")
                            
                        with ui.row():
                            # if migration_job.status != Status.APPROVED and migration_job.status != Status.COMPLETED:
                            ui.button('Confirm',icon="check", on_click=_update_migration_job ).props('positive').classes('bg-positive text-white')
                            ui.button('Cancel', on_click=dialog.close).props("primary")
                    
                    dialog.open()
                    
                # _ids = [r.get('id') for r in table_of_results.selected]
                # _data = [l for l in list_of_apps if l.get('id') in _ids]
                ui.label("Review Selected Apps").classes('font-bold text-lg')
                _json_applications = ui.json_editor({'content': {'json': table_of_results.selected}})
                ui.label("Review Selected Service Principals").classes('font-bold text-lg')
                _json_service_principals = ui.json_editor({'content': {'json': table_of_results.selected}})
                
                # TEMP
                ui_helper.alert_info("If apps are not showing in JSON editor, go back then forward to refresh the data.")
                
                
                with ui.stepper_navigation():

                    ui.button('Save', on_click= _confirm_submit_json_data ).classes("bg-positive text-white")
                    ui.button('Back', on_click=stepper.previous).props('flat')
