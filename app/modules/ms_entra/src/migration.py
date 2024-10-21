from fastapi.responses import JSONResponse

from typing import Dict

from core.utils.database import Database, ObjectId
from core.common import log, print

from ..src import utils, msapp
from ..schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions


async def update_migration_job(id:str, job_json:dict) -> None:
    """
    Update a migration job. May provide only specific fields to update.
    Does not validate the data, so make sure the data is validated already before calling this function.
    """
    if not job_json:
        raise Exception("No job data found")    
    
    try:
        
        # job = MigrationJob(**job_json)
        # Set up DB client
        db_client = Database.get_collection(MigrationJob.Settings.name)
        
        # Update
        # res = db_client.update_one({'_id': ObjectId(id) }, {"$set": {"apps": data, "status": Status.PENDING_APPROVAL.value }})
        res = db_client.update_one({'_id': ObjectId(id) }, {"$set": job_json })
        
        return JSONResponse(content={"message": f"Migration Job updated: {res}"})
        
    except Exception as e:
        raise Exception(e)


def save_execution(job: MigrationJob):
    return update_migration_object(job)

def update_migration_object(job: MigrationJob):
    db = Database.get_collection(MigrationJob.Settings.name)
    db.update_one({"_id": ObjectId(job.id)}, {"$set": job.model_dump(exclude=["source_tenant", "destination_tenants", "name","search_params", 'migration_options'])})

