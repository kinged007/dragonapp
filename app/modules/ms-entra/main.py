"""
This is an example module for a bookshelf application.
"""
from fastapi import APIRouter
# from datetime import date
from typing import List, Optional, Dict, Any, Union, Optional, List
from pydantic import BaseModel, Field, SecretStr, EmailStr, AnyUrl, AnyHttpUrl
import json

from core import Module
from core.utils.logging import logger as log
from core.schemas import database, module_config
from core.utils.endpoints import CRUDJsonEndpoints

# AdminPanel UI
from core.modules.admin_panel import AdminPanel, ui
from .migrate_edit import router as ms_entra_migrate_edit
from .migrate_exec import router as ms_entra_migrate_exec

from .schema import Tenant, MigrationJob, SearchTemplates

# Define the configuration class
class MSEntraConfig(module_config.BaseModuleConfig):
    """
    Configuration options for the MS Entra Tenant Migration module
    """
    # Add configuration options here
    pass


   

# Define the API router
api_router = APIRouter()

# Define the CRUD endpoints
CRUDJsonEndpoints(
    api_router,
    base_name="MS Entra",
    collection=[Tenant,MigrationJob, SearchTemplates],
    # database=[Author, Publisher, Tag, Book],
    method=['GET', 'POST', 'PATCH', 'DELETE'],
    # tags=['Bookshelf'], # Auto tag
    # name_singluar='Book', # Auto apply
    # name_plural='Books', # temp
).build()


def edit_migration_details(item: dict, base_model: database.DatabaseMongoBaseModel ):
    if base_model.collection_name() == "ms_entra_migration_job":
        job = MigrationJob(**item)
        log.warning(f"Callback 'crud_item_created' executed: {item}")
        # print(type(job), job)
        # print(job.name)
        ui.navigate.to(f"/ms-entra/migrate-job/edit/{job.id}")
        # with ui.dialog() as dialog, ui.card():
        #     ui.label(f"New Migration Job Created: {job.id}")
        # dialog.open()

def crud_interface_buttons(base_model: database.DatabaseMongoBaseModel, selected_items = None):
    if base_model.collection_name() == "ms_entra_migration_job":
        
        def _click_edit():
            if selected_items:
                # ui.notification("Click!", position='center', type='positive', icon='check', timeout=1)
                item = selected_items()
                if len(item) != 1:
                    ui.notification("Select a single item to modify.", position='center', type='negative', icon='error', timeout=1)
                    return
                job = MigrationJob(**item[0])   
                ui.navigate.to(f"/ms-entra/migrate-job/edit/{job.id}")
                
        def _click_exec():
            if selected_items:
                # ui.notification("Click!", position='center', type='positive', icon='check', timeout=1)
                item = selected_items()
                if len(item) != 1:
                    ui.notification("Select a single item to modify.", position='center', type='negative', icon='error', timeout=1)
                    return
                job = MigrationJob(**item[0])   
                if job.status != "APPROVED":
                    ui.notification("Job must be in 'APPROVED' status to execute.", position='center', type='negative', icon='error', timeout=1)
                    return
                
                ui.navigate.to(f"/ms-entra/migrate-job/execute/{job.id}")

        ui.button("Edit Job Details", on_click=_click_edit)
        ui.button("Execute Job", on_click=_click_exec)


# Define the module
Module.register(
    __name__,
    title='MS Entra Migration Helper',
    config_class=MSEntraConfig,
    database=[Tenant, MigrationJob, SearchTemplates],
    description="MS Entra ID Tenant Migration Helper.",
    version="0.1.0",
    router=api_router,
    events=[
        # ('event_name', callback_function)
        ('crud_item_created', edit_migration_details ),
        ('crud_item_modified', edit_migration_details ),
        ('crud_interface_top_left', crud_interface_buttons ),
    ],    
)

AdminPanel.include_router(ms_entra_migrate_edit, prefix='/ms-entra/migrate-job', tags=["MS Entra"], dependencies=None)
AdminPanel.include_router(ms_entra_migrate_exec, prefix='/ms-entra/migrate-job', tags=["MS Entra"], dependencies=None)