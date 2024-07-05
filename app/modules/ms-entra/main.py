"""
This is an example module for a bookshelf application.
"""
from fastapi import APIRouter
# from datetime import date
from typing import List, Optional, Dict, Any, Union, Optional, List
from pydantic import BaseModel, Field, SecretStr, EmailStr, AnyUrl, AnyHttpUrl
import asyncio

from core import Module
from core.utils.logging import logger as log
from core.schemas import database, module_config
from core.utils.endpoints import CRUDJsonEndpoints

# AdminPanel UI
from core.modules.admin_panel import AdminPanel, ui
from .migration_job import router as ms_entra_migrate_edit
# from .migrate_exec import router as ms_entra_migrate_exec

from .schema import Tenant, MigrationJob, SearchTemplates
from .hooks import edit_migration_details, crud_interface_buttons, edit_migration_details

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
# AdminPanel.include_router(ms_entra_migrate_exec, prefix='/ms-entra/migrate-job', tags=["MS Entra"], dependencies=None)