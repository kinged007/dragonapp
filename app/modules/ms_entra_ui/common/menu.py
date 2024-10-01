from nicegui import ui
from core import Module, log
from core.utils.string import to_snake_case
from beanie import Document # TODO Deprecate
from core.schemas.database import DatabaseMongoBaseModel
from core.events import trigger_event

def sidebar_menu(self):
    
    _menu = {
        "Dashboard" : "/",
        "New Request" : "/ticket/new",
        "Tickets" : "/collection/ms_entra/ms_entra_migration_job",
        "Tools" : {
            "Tenants" : "/collection/ms_entra/ms_entra_tenants",
            "App Explorer" : "/tool/app-explorer",
            "Terminal" : "/tool/terminal",
            "Logs" : "/tool/logs",
            "Settings" : "/tool/settings",
        },
    }
    
    
    # for module in Module.modules.values():
    #     if module.database:
            
    #         # with ui.expansion(module.title, icon="").classes('full-width text-light'):
    #         for db in module.database:
    #             # Check type of database, eg. MongoDB Document, or SQL Table
    #             db_name = db_title = None
                
    #             try:
    #                 if issubclass(db, DatabaseMongoBaseModel):
    #                     db_name = db.Settings.name
    #                     db_title = db.Settings.title if hasattr(db.Settings, 'title') else to_snake_case(db_name)
                    
    #                 if db_name:
    #                     _t = module.title if hasattr(module, 'title') else to_snake_case(module.name)
    #                     _url_path = f"/collection/{module.name}/{db_name}"
    #                     if _t not in _menu:
    #                         _menu[_t] = {}
    #                     _menu[_t][db_title] = _url_path
    #             except Exception as e:
    #                 log.error(e)
    
    
    # Trigger event hook
    trigger_event("frontend_pre_sidebar_menu", menu=_menu )
    
    for title, url in _menu.items():
        
        if isinstance(url, dict):
            with ui.expansion(title, icon="").classes('full-width text-light'):
                for db_title, _url_path in url.items():
                    ui.menu_item(db_title, on_click=lambda url_path=_url_path: ui.navigate.to(url_path)).classes('full-width')
                    # ui.menu_item(db_title, on_click=lambda url_path=_url_path: ui.navigate.to(url_path)).classes('full-width')
        else:
            ui.menu_item(title, on_click=lambda url_path=url: ui.navigate.to(url_path)).classes('full-width text-light')
            # ui.menu_item(title, on_click=lambda: ui.navigate.to(url)).classes('full-width text-light')
        
            
    # Trigger menu event hook
    trigger_event("frontend_post_sidebar_menu")
    
    # TODO If SuperAdmin. Move Settings to bottom of sidebar into icon
    ui.menu_item("Settings", on_click=lambda: ui.navigate.to(f"/config/module")).classes('full-width text-light')
    
    # Place Modules settings at bottom of sidebar
    # with ui.column().classes('full-width'):
        # with ui.expansion("Modules", icon="extension").classes('full-width text-light'):
        #     for module in Module.loaded_modules:
        #         _module_name = to_snake_case(module)
        #         ui.menu_item(_module_name, on_click=lambda module=module: ui.navigate.to(f"/config/module/{module}")).classes('full-width')
        