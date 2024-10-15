"""
Migration logic for the module. Used in an async function.
Accepts MigrationJob object as argument.
Yields Text/log entries to be displayed in the frontend.

- Check displayName does not exist
- create apps
- populate with metadata
- check for errors
- post-process apps

- check SP for duplicates
- create SP
- populate with metadata
- check for errors
- post-process SP

"""

from ..schema import MigrationJob
from core.utils.datetime import nice_time
from ..src.migration import save_execution
from core import log, print
from ..schema import Tenant, Status, MigrationJob, MigrationOptions
from ..src import utils, msapp
from ..schema import Tenant, MigrationJob, Status, SearchTemplates, MigrationOptions, AppsType
import asyncio
from ..models.applications import ApplicationModel
from ..models.service_principals import ServicePrincipalModel
from ..src.msapp import connect_tenant


async def migrate(job: MigrationJob):
    """
    
    """
    output_log = job.log

    def _log(msg):
        """ Log a message to the console and the migration job log. """
        _m = f"{nice_time()} | {msg}"
        job.log.append(_m)
        print(_m)
        yield _m
    
    def _error(msg):
        """ Log an error message to the console and the migration job log. """
        job.error_log.append(f"{nice_time()} | ERROR: {msg}")
        _log(f"ERROR: {msg}")


    tenants = []
    
    for dest in job.destination_tenants:
        
        try:
            
            _dest_tenant:Tenant = connect_tenant(dest.model_dump())
                        
            if not _dest_tenant.access_token:
                raise 
            
            tenants.append(_dest_tenant)
            
        except Exception as e:
            raise Exception(f"Failed to connect to destination tenant: {dest.name}")
    
    for dest_tenant in tenants:
        
        # type declaration
        dest_tenant: Tenant
        
        _log(f"Connecting to {dest_tenant.name}")
        await asyncio.sleep(0.5)
        
        try:
            
            # Migrate apps
            apps = job.apps if job.apps_type == AppsType.applications else job.service_principals
            job.status = Status.IN_PROGRESS

            yield f"Migrating '{len(apps)}' '{job.apps_type}' to '{dest_tenant.name}'"
            await asyncio.sleep(1)
                

            for i in range(len(apps)):
                
                try:
                    
                    yield f"Parsing {job.apps_type} app data for {apps[i].get('displayName','?')}"
                    await asyncio.sleep(0.3)
                    # console.print(apps[i])
                    if job.apps_type == AppsType.applications:
                        _data = ApplicationModel(**apps[i])
                    elif job.apps_type == AppsType.servicePrincipals:
                        _data = ServicePrincipalModel(**apps[i])
                    else:
                        raise Exception("Error in table format. Invalid AppsType")
                    # console.print(_data.post_model())
                    
                except Exception as e: 
                    yield f"❌ Failed to parse app data for {apps[i].get('displayName','?')}: {e}"
                    await asyncio.sleep(0.1)
                    continue
                
                source_app_data = _data.model_copy()
        
        except Exception as e:
            yield f"❌ Failed to migrate apps: {e}"
            job.status = Status.FAILED
            break

    # ### Migrate Apps
    # if job.stage == 'apps':
        
    #     _log("Executing App Migration...")
    #     async for result in msapp.process_migration_job(job):
    #         _log(job.apps_type + " | " + result)
        
    #     _log("Migration of Apps is Complete.")
    #     _log(f"Execution status: {job.status}")
        
    #     if job.status == Status.COMPLETED:
    #         job.stage = 'post_apps'
            
    #     # Update
    #     save_execution(job)
