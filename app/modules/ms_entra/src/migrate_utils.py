
from typing import Union
import asyncio
from ..models.applications import ApplicationModel
from ..models.service_principals import ServicePrincipalModel
from ..schema import Tenant, MigrationJob, MigrationOptions, AppsType
from ..src.msapp import server_request

async def validate_apps(apps: dict, type: AppsType):
    """
    Validate the apps before migrating.
    """
    for i in range(len(apps)):
        print( f"Validating {type} app data for {apps[i].get('displayName','?')}")
        await asyncio.sleep(0.3)
        # console.print(apps[i])
        if type == AppsType.applications:
            app = ApplicationModel(**apps[i])
        elif type == AppsType.servicePrincipals:
            app = ServicePrincipalModel(**apps[i])
        else:
            raise Exception("Error in table format. Invalid AppsType")
        
        yield app
        
def get_existing_app(app: Union[ApplicationModel,ServicePrincipalModel], tenant: Tenant, job: MigrationJob):
    """
    Check if the app already exists in the tenant.
    Uses the saved id mapping object to check if the app already exists.
    TODO - Check if the app exists in the tenant by querying the tenant.
    """
    _reference_attribute = job.migration_options.reference_attribute #"appId" # or "displayName"
    # Existing app in the destination tenant
    if type(app) == ApplicationModel:
        _existing_app = job.app_id_mapping.get(getattr(app,_reference_attribute),{}).get(tenant.client_id, None)
        if _existing_app and 'data' in _existing_app:
            return ApplicationModel(**_existing_app.get('data'))
    else :
        _existing_app = job.sp_id_mapping.get(getattr(app,_reference_attribute),{}).get(tenant.client_id,None)
        if _existing_app and 'data' in _existing_app:
            return ServicePrincipalModel(**_existing_app.get('data'))

    # if _existing_app and 'data' in _existing_app:
    #     return _existing_app.get('data')
    
    return False






def prepare_app(app: Union[ApplicationModel,ServicePrincipalModel], job: MigrationJob):
    """ 
    Prepares the app for migration, incorporating migration options etc.
    """
    _type = "applications" if type(app) == ApplicationModel else "servicePrincipals"
    _ops:MigrationOptions = job.migration_options
    app.displayName = f"{app.displayName} {_ops.new_app_suffix}"
    return app

async def create_app(app: Union[ApplicationModel,ServicePrincipalModel], tenant: Tenant, job: MigrationJob):
    """
    Create the app to the tenant.
    """
    _type = "applications" if type(app) == ApplicationModel else "servicePrincipals"
    endpoint = f"{tenant.endpoint}/{_type}"
    _ref = job.migration_options.reference_attribute 
    _original_ref = getattr(app,_ref)

    req = server_request(
        endpoint, 
        method="POST", 
        data=app.model_dump(include=["displayName"]), 
        api_key=tenant.access_token, 
        # host=dest_tenant.endpoint
    )
                    
    # Success
    if req and req.status_code == 201:
        # Check emoji: https://emojicombos.com/
        # Store successful migration in migration job.
        _new_app_id = req.json().get('appId')
        if not _new_app_id:
            raise Exception(f"Failed to get new app id for newly created app: {req.json()}")

        _new_app = req.json()
        _new_app.update({"original_ref": _original_ref})
        
        # Applications
        if type(app) == ApplicationModel:
            if getattr(app,_ref) not in job.app_id_mapping: 
                job.app_id_mapping[_original_ref] = {}
            job.app_id_mapping[_original_ref].update({tenant.client_id: {"appId": _new_app_id, "data": _new_app }})
        
        # Service Principals
        if type(app) == ServicePrincipalModel:
            if getattr(app,_ref) not in job.sp_id_mapping:
                job.sp_id_mapping[_original_ref] = {}
            job.sp_id_mapping[_original_ref].update({tenant.client_id: {"appId": _new_app_id, "data": _new_app }})

        return req.json()
    
    # Failure
    else:
        raise Exception(f"Failed to create app: {req.json()}")



async def update_app(app: Union[ApplicationModel,ServicePrincipalModel], tenant: Tenant, job: MigrationJob):
    """
    Update the app to the tenant.
    TODO Loop through parameters and update one by one. Failed updates should be logged to update or ignore later.
    Save to job.logs using LogModel model
    
    """
    _type = "applications" if type(app) == ApplicationModel else "servicePrincipals"
    endpoint = f"{tenant.endpoint}/{_type}(appId='{app.appId}')"
    _ref = job.migration_options.reference_attribute 
    _original_ref = app.original_ref or getattr(app,_ref)

    yield "Updating App on Tenant..."
    
    req = server_request(
        endpoint, 
        method="PATCH", 
        data=app.post_model(['passwordCredentials','keyCredentials','identifierUris']), 
        api_key=tenant.access_token, 
        # host=dest_tenant.endpoint
    )
    print("DEBUG POSTMODEL", app.post_model(['passwordCredentials','keyCredentials','identifierUris']))
    # Success - No content
    if req and req.status_code == 204:
        
        yield "App Updated Successfully."
        
        # Fetch the app
        req2 = server_request(
            endpoint, 
            method="GET", 
            api_key=tenant.access_token, 
            # host=dest_tenant.endpoint
        )
        
        if req2 and req2.status_code == 200:
            # Sucess
            _new_app = req2.json()
            
            if not _new_app:
                raise Exception(f"Failed to get updated app: {req2.json()}")
            
            _new_app.update({"original_ref": _original_ref})
            
            # Applications
            if type(app) == ApplicationModel:
                job.app_id_mapping[_original_ref].update({tenant.client_id: {"data": _new_app }})
                yield ApplicationModel(**_new_app)
            
            # Service Principals
            if type(app) == ServicePrincipalModel:
                job.sp_id_mapping[_original_ref].update({tenant.client_id: {"data": _new_app }})
                yield ServicePrincipalModel(**_new_app)
            
        else:
            raise Exception(f"Failed to get updated app: {req2.json()}")
    
    # Failure
    else:
        raise Exception(f"Failed to update app: {req.json()}")
