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

@api_router.get("/test")
async def test(id: str):
    from .src.migrate import migrate_execution
    from core.utils.database import Database, ObjectId
    db = Database.get_collection(MigrationJob.Settings.name)
    job = db.find_one({"_id": ObjectId(id)})
    migration_job = MigrationJob(**job)
    # res = migrate_execution(migration_job)
    output = []
    # Running the migration asynchronously
    async for res in migrate_execution(migration_job):
        output.append(res)
    
    # Running the migration in the background
    
    return {"message": output }

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

AdminPanel.include_router(ms_entra_migrate_edit, prefix='/ms_entra/migrate-job', tags=["MS Entra"], dependencies=None)
# AdminPanel.include_router(ms_entra_migrate_exec, prefix='/ms_entra/migrate-job', tags=["MS Entra"], dependencies=None)