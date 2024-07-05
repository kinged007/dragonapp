from fastapi.responses import JSONResponse

from typing import Dict

from core.utils.database import Database, ObjectId
from core.common import log, print

from ..src import utils, msapp
from ..schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions


async def update_migration_job(job_json:dict) -> None:

    if not job_json:
        raise Exception("No job data found")    
    
    try:
        
        job = MigrationJob(**job_json)
        # Set up DB client
        db_client = Database.get_collection('ms_entra_migration_job')
        
        # Update
        # res = db_client.update_one({'_id': ObjectId(id) }, {"$set": {"apps": data, "status": Status.PENDING_APPROVAL.value }})
        res = db_client.update_one({'_id': ObjectId(job.id) }, {"$set": job.model_dump() })
        
        return JSONResponse(content={"message": f"Migration Job updated: {res}"})
        
    except Exception as e:
        raise Exception(e)
