import asyncio, json
from core.utils.frontend import ui_helper, ui, FormBuilder
from core.utils.database import Database
from core import log, print
from ..schema import Tenant, Status, MigrationJob, MigrationOptions
from ..src import utils, msapp
from ..schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions
from ..src.migration import update_migration_job
from ..schema import Tenant, MigrationJob, Status, AppsType
from ..models.applications import ApplicationModel, passwordCredentialResource, keyCredentialResource
from ..models.service_principals import ServicePrincipalModel



def migrate_tab_edit(migration_job: MigrationJob, source_tenant: Tenant):
    

    # - Edit
    #     - Search
    #     - Select
    #     - Review
    #     - Options

    with ui.tabs().classes() as tabs:
        review = ui.tab('Review')
        options = ui.tab('Options')
        search = ui.tab('Search')
        json_paste = ui.tab('JSON')


    if migration_job.status == Status.APPROVED or migration_job.status == Status.COMPLETED:
        ui_helper.alert_warning(f"This JOB can not be modified. Current Status: {migration_job.status}. Change to PENDING to modify.")
        # TODO Check if user is Admin or Owner, in which case they may be able to modify it!
        # if Permission.write(migration_job.id): ...

    list_of_apps = []
    

    
    
    with ui.tab_panels(tabs, value=review).props('q-pa-none').classes('full-width').style("background: none;"):
            
        with ui.tab_panel(review).props('q-pa-none'):
            # Review Migration and Apps. Editing of JSON allowed.
            ui.label(f"Migration Job: {migration_job.name}")
            ui.label(f"Status: {migration_job.status}") # TODO Allow to change status if user is Admin or Owner, in which case they may be able to modify it!
            ui.label(f"Stage: {migration_job.stage.capitalize()}")
            ui.label(f"Source Tenant: {source_tenant.name}")
            ui.label(f"Destination Tenants: {', '.join([t.name for t in migration_job.destination_tenants])}")
            ui.label("Migration Options")
            ui.json_editor({'content':{'json': migration_job.migration_options.model_dump()}})
            ui.separator()
            ui.label(f"Apps to Migrate: {len(migration_job.apps)}")
            ui.label(f"Apps Type: {migration_job.apps_type}")
            ui.label("App Registrations")
            ui.json_editor({'content':{'json': migration_job.apps}})
            ui.label("Service Principals")
            ui.json_editor({'content':{'json': migration_job.service_principals}})
            
            ui.separator() 
            
            # if migration_job.status == Status.PENDING_APPROVAL:
            #     ui.button("Approve Migration Job", on_click=_approve_job).classes("bg-positive text-white")
            

        with ui.tab_panel(options).props('q-pa-none'):
            
            async def _update_options() -> None:
    
                async def _update_options_confirmed() -> None:

                    migration_job.migration_options = MigrationOptions(**form_migration_options.current_values)
                    
                    # Update
                    try:
                        await update_migration_job(migration_job.id, migration_job.model_dump(include=['migration_options']))
                        ui.notify("Migration Job Updated!", type='positive')
                        print("SAVE MIGRATION JOB GOOD", migration_job)
                        dialog.close()
                        
                        # ui.navigate.to(f"/ms-entra/migrate-job/{migration_job.id}?tab=approve")
                        
                    except Exception as e:
                        log.error(e)
                        ui.notify(f"Failed to update Migration Job: {e}", type='negative')
                        print("SAVE MIGRATION JOB FAIL", migration_job)
                        dialog.close()
                                                            
                with ui.dialog() as dialog, ui.card():
                    ui.label('Confirm?')
                    if migration_job.status == Status.APPROVED or migration_job.status == Status.COMPLETED:
                        ui_helper.alert_warning(f"This JOB can not be modified. Current Status: {migration_job.status}")
                        
                    with ui.row():
                        if migration_job.status != Status.APPROVED and migration_job.status != Status.COMPLETED:
                            ui.button('Confirm',icon="check", on_click=_update_options_confirmed ).props('positive').classes('bg-positive text-white')
                        ui.button('Cancel', on_click=dialog.close).props("primary")
                
                dialog.open()

            # with ui.column().classes('full-width'):
                
            #   Review Migration Options
            # ui.label("Migration Options").classes('font-bold text-lg')
            _schema = MigrationOptions.model_json_schema()
            # print(_schema)
            # print("PARSED SCHEMA", ui_helper.json_schema_parser(_schema))
            form_migration_options = FormBuilder(_schema, migration_job.migration_options.model_dump() )
            form_migration_options.submit_value = None
            form_migration_options.build_main_form()
            
            if migration_job.status != Status.APPROVED and migration_job.status != Status.COMPLETED:
                ui.button('Save Changes', on_click=_update_options ).classes("bg-positive text-white")
                
        with ui.tab_panel(search).props('q-pa-none'):
                
            with ui.column():

                with ui.stepper().props().classes('w-full full-width') as stepper:
                    
                    with ui.step('Search Criteria'):

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
                            # _json_editor_results.set({'content': {'json': [l for l in list_of_apps if l.get('id') in _ids]}}) 
                            stepper.next()
                            # stepper.previous()
                            # stepper.next()
                            # _json_editor_results.run_editor_method('updateProps', {'content': {'json': [l for l in list_of_apps if l.get('id') in _ids]}})

                        app_type = migration_job.apps_type
                                                
                        # ui.label(f"Searching '{app_type}' from Tenant '{source_tenant.name}'").classes('font-bold text-lg')
                        ui.label(f"Search for Apps on Tenant '{source_tenant.name}'").classes('font-bold text-lg')
                        
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
                            _app_type = ui.select(label="App Type", options=['applications','servicePrincipals'], value=migration_job.apps_type.value).classes("full-width")
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
                                                    
                        async def _confirm_submit_json_data() -> None:
                            
                            async def _update_migration_job() -> None:
                                data = await _json_editor_results.run_editor_method('get')
                                data = data.get('json',[])
                                if not data or len(data) == 0:
                                    ui.notify("No data selected!")
                                    return
                                
                            
                                migration_job.apps_type = _app_type.value
                                if migration_job.apps_type == 'servicePrincipals':
                                    migration_job.service_principals = data
                                else:
                                    migration_job.apps = data
                                migration_job.status = Status.PENDING_APPROVAL
                                migration_job.search_params = {
                                    "search": _search.value,
                                    "filter": _filter.value,
                                    "raw": _raw.value,
                                    "skip_publishers": _skip_publishers.value if _skip_publishers and _app_type.value == 'servicePrincipals' else [],
                                }
                                migration_job.migration_options = MigrationOptions(**form_migration_options.current_values)
                                
                                # Update
                                try:
                                    await update_migration_job(migration_job.id, migration_job.model_dump())
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
                                ui.label('Are you sure you want to migrate these apps and save the Options?')
                                if migration_job.status == Status.APPROVED or migration_job.status == Status.COMPLETED:
                                    ui_helper.alert_warning(f"This JOB can not be modified. Current Status: {migration_job.status}")
                                    
                                with ui.row():
                                    if migration_job.status != Status.APPROVED and migration_job.status != Status.COMPLETED:
                                        ui.button('Confirm',icon="check", on_click=_update_migration_job ).props('positive').classes('bg-positive text-white')
                                    ui.button('Cancel', on_click=dialog.close).props("primary")
                            
                            dialog.open()
                        # _ids = [r.get('id') for r in table_of_results.selected]
                        # _data = [l for l in list_of_apps if l.get('id') in _ids]
                        _json_editor_results = ui.json_editor({'content': {'json': table_of_results.selected}})
                        
                        # TEMP
                        ui_helper.alert_info("If apps are not showing in JSON editor, go back then forward to refresh the data.")
                        
                        with ui.stepper_navigation():

                            ui.button('Save', on_click= _confirm_submit_json_data ).classes("bg-positive text-white")
                            ui.button('Back', on_click=stepper.previous).props('flat')

        with ui.tab_panel(json_paste).props('q-pa-none'):
            
            ui_helper.alert_info("Paste JSON data of applications that you want to migrate. The JSON string MUST be collected using Microsoft Graph API.")
            
                
                
                
            async def _save_pasted_json():

                async def _update_migration_job_app_paste():
                    if _d:
                        migration_job.apps_type = AppsType.applications
                        migration_job.apps = _d
                    if _d2:
                        migration_job.service_principals = _d2
                    if _d and not _d2:
                        migration_job.apps_type = AppsType.servicePrincipals
                    migration_job.status = Status.PENDING_APPROVAL
                    migration_job.migration_options = MigrationOptions(**form_migration_options.current_values)

                    # Update
                    try:
                        await update_migration_job(migration_job.id, migration_job.model_dump())
                        ui.notify("Migration Job Updated!", type='positive')
                        print("SAVE MIGRATION JOB GOOD", migration_job)
                        dialog_save_json.close()
                        
                        ui.navigate.to(f"/ms-entra/migrate-job/{migration_job.id}?tab=approve")
                        
                    except Exception as e:
                        log.error(e)
                        ui.notify(f"Failed to update Migration Job: {e}", type='negative')
                        print("SAVE MIGRATION JOB FAIL", migration_job)
                        dialog_save_json.close()


                # json_pasted_apps.run_editor_method('updateProps', {'mode': 'tree'})
                data = await json_pasted_apps.run_editor_method('get')
                _d = data.get('json', []) if 'json' in data else data.get('text', "") if 'text' in data else []
                # if not _d:
                #     ui.notify("No data found!")
                #     return
                data = await json_pasted_sp.run_editor_method('get') # optional
                _d2 = data.get('json', []) if 'json' in data else data.get('text', "") if 'text' in data else []
                # if not _d2:
                #     ui.notify("No data found!")
                #     return
                
                try:
                    
                    if isinstance(_d, str):
                        _d = json.loads(_d)
                    if isinstance(_d, list):
                        _d = _d
                    elif isinstance(_d, dict):
                        _d = [_d]
                    else:
                        raise Exception("Invalid JSON App data!")
                    # _data1 = ApplicationModel(**_d[0])
                    # if not _data1.displayName or not _data1.appId:
                    #     raise Exception("appId and displayName are required fields! Please check the JSON data.")

                    if _d2 and isinstance(_d2, str):
                        _d2 = json.loads(_d2)
                    if isinstance(_d2, list):
                        _d2 = _d2
                    elif isinstance(_d2, dict):
                        _d2 = [_d2]
                    else:
                        raise Exception("Invalid JSON Service Principal data!")
                        
                        # _data2 = ServicePrincipalModel(**_d2[0])

                        # if not _data2.displayName or not _data2.appId:
                        #     raise Exception("appId and displayName are required fields! Please check the JSON data.")

                    
                    ## Save
                    with ui.dialog() as dialog_save_json, ui.card():
                        ui.label('Are you sure you want to use this pasted JSON instead?')
                        ui_helper.alert_warning(f"This will overwrite any previously saved app metadata.")
                            
                        with ui.row():
                            ui.button('Confirm',icon="check", on_click=_update_migration_job_app_paste ).props('positive').classes('bg-positive text-white')
                            ui.button('Cancel', on_click=dialog_save_json.close).props("primary")
                    
                    dialog_save_json.open()
                    
                except Exception as e:
                    ui.notify(e)
                    return
                    
                print(type(_d))
                # ui.notify(_d)
            
            ui.label("Paste JSON Data for App Registrations").classes('font-bold text-lg')
            
            json_pasted_apps = ui.json_editor({'content': {'json': []} }) #, "mode":'text'} )
            # json_pasted_apps.run_editor_method('updateProps', {'text': True})
            
            ui.label("Paste JSON Data for Service Principals").classes('font-bold text-lg')
            ui.label("Service Principals should be related to the App Registrations.")
            
            json_pasted_sp = ui.json_editor({'content': {'json': []} }) #, "mode":'text'} )
            
            ui.button('Save', on_click= _save_pasted_json ).classes("bg-positive text-white")
            
            pass
