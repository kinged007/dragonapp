from enum import Enum
from typing import List, Optional, Dict, Any, Union, Optional, List, Literal
from pydantic import BaseModel, Field, SecretStr, EmailStr, AnyUrl, AnyHttpUrl, root_validator
import json
from core.schemas import database
from .src.utils import dict_diff
from core import log, print

class Status(str, Enum):
    """
    Job Status options for Migration Job
    Workflow:
        0. Create New Migration Job, redirects to this page
        1. Job Overview (includes report and diffs, and remove apps button on dest tenants)
        2. Migration Options
        3a. Search Criteria
            3b. Select Apps
        4. Review Apps
        6. Approve App Migration
        7. Execute App Migration
        8. Review ServicePrincipal Migration (can edit)
        9. Execute ServicePrincipal Migration
        10. Final Report
    """
    PENDING = "PENDING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    
    # Revised
    # PENDING_APPROVAL_APPS = "PENDING_APPROVAL_APPS"
    # PENDING_APPROVAL_SERVICE_PRINCIPALS = "PENDING_APPROVAL_SERVICE_PRINCIPALS"
    # APPROVED_APPS = "APPROVED_APPS"
    # APPROVED_SERVICE_PRINCIPALS = "APPROVED_SERVICE_PRINCIPALS"
    # IN_PROGRESS_APPS = "IN_PROGRESS_APPS"
    # IN_PROGRESS_SERVICE_PRINCIPALS = "IN_PROGRESS_SERVICE_PRINCIPALS"
    # COMPLETED_APPS = "COMPLETED_APPS"
    # COMPLETED_SERVICE_PRINCIPALS = "COMPLETED_SERVICE_PRINCIPALS"
    # FAILED = "FAILED"
    # CANCELLED = "CANCELLED"
    
  
class AppsType(str, Enum):
    servicePrincipals = "servicePrincipals"
    applications = "applications"
    
    
# Define the database tables
class Tenant(database.DatabaseMongoBaseModel):
    name: str = Field(..., description="The name of the tenant")
    description: Optional[str] = Field(None, description="The description of the tenant")
    authority: str = Field(..., description="The authority of the tenant")
    client_id: str = Field(..., description="The client ID of the tenant")
    scope: List[str] = Field(["https://graph.microsoft.com/.default"], description="The scope of the tenant")
    secret: str = Field(..., description="The secret of the tenant", json_schema_extra={"format": "password", "password_visible": True}) # TODO Make secret not visible
    endpoint: str = Field("https://graph.microsoft.com/v1.0", description="The base URL of the tenant. Define here /v1.0 or /beta.")
    # created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="The creation time of the tenant")
    # file: Optional[str] = Field(None, description="The name of the tenant")
    access_token: Optional[str] = Field(None, description="The access token of the tenant", json_schema_extra={"hidden": True,  "password_visible": False})
    
    @root_validator
    def fix_endpoint(cls, values):
        """Simply ensures that the endpoint url has dropped the last slash if it exists"""
        if 'endpoint' in values:
            values['endpoint'] = values['endpoint'].rstrip('/')
        return values
        
    class Settings:
        name = "ms_entra_tenants"
        title = "Entra Tenants"
        
    class Config:
        # Required for database references
        json_schema_extra = {
            "collection_name": "ms_entra_tenants",
            "type": "database_ref",
            "display_field": "{name}"
        }
        
    

# Migration Job

class MigrationOptions(BaseModel):
    """
    Migration Options
    """
    skip_expired_credentials: bool = Field(True, description="Skip expired credentials")
    generate_new_password_if_all_expired: bool = Field(False, description="Generate new password if all are expired")
    generate_new_certificate_if_all_expired: bool = Field(False, description="Generate new certificate if all are expired")
    new_app_suffix: str = Field("", description="The suffix to add to the new app name")
    app_naming_template: str = Field("{displayName}", description="The naming template for the new app. Use Microsoft Graph API parameters.") # eg. 
    use_upsert: bool = Field(False, description="Use upsert to update existing apps or create new one if they don't exist")
    migrate_service_principals: bool = Field(True, description="Migrate service principals after Applications have been migrated successfully.")
    # create group and assign to app (app/SP?)
    
    
    
            
class MigrationJob(database.DatabaseMongoBaseModel):
    
    
    name: str = Field(..., description="The name of the migration job")
    status: Status = Field(Status.PENDING, description="The status of the migration job")
    apps_type: AppsType = Field(AppsType.applications, description="The type of apps to be migrated")
    stage: Literal['pending','apps','post_apps','service_principals_from_apps', 'service_principals','post_service_principals','completed'] = Field('pending', description="The stage of the migration job")
    search_params: Optional[Dict] = Field({}, description="The search parameters for the apps to be migrated", json_schema_extra={"hidden": True})
    
    apps: List[Dict] = Field([], description="The apps to be migrated", json_schema_extra={"hidden": True}) 
    service_principals: List[Dict] = Field([], description="The service principals to be migrated", json_schema_extra={"hidden": True}) 
    
    # file: Optional[str] = None
    source_tenant: Optional[List[Tenant]] = Field(None, description="The source tenant file name")
    # source_client_id: Optional[str] = Field(default=None, description="The source tenant client id")
    destination_tenants: List[Tenant] = Field([], description="The destination tenant file names")
    migration_options: Optional[MigrationOptions] = Field(MigrationOptions(), description="The migration options")
    
    app_id_mapping: Optional[Dict[str, Dict[str, dict]]] = Field({}, description="The mapping of app ids between source and destination tenants: {source_app_id:  {destination_client_id: destination_app_id}}", json_schema_extra={"hidden": True})
    sp_id_mapping: Optional[Dict[str, Dict[str, dict]]] = Field({}, description="The mapping of app ids between source and destination tenants: {source_app_id:  {destination_client_id: destination_app_id}}", json_schema_extra={"hidden": True})
    # apps_migrated: List[str] = Field([], description="The list of apps that have been migrated")
    apps_failed: Optional[Dict[str, Dict[str,dict]]] = Field({}, description="The list of apps that failed to migrate: {destination_client_id: {'app': _data, 'response': req.text, 'status': req.status_code }}", json_schema_extra={"hidden": True})
    sp_failed: Optional[Dict[str, Dict[str,dict]]] = Field({}, description="The list of apps that failed to migrate: {destination_client_id: {'app': _data, 'response': req.text, 'status': req.status_code }}", json_schema_extra={"hidden": True})
    
    log: Optional[List[str]] = Field([], description="The log of the migration job")
    
    class Settings:
        name = "ms_entra_migration_job"
        title = "Entra Migration Job"
        
    class Config:
        # Required for database references
        json_schema_extra = {
            "collection_name": "ms_entra_migration_job",
            "type": "database_ref",
            "display_field": "{name}"
        }
        
    def save(self):
        # Save to file Deprecated??
        if not self.file:
            raise Exception("Set a `file` name first.")
        with open(self.file, "w") as f:
            json.dump(self.model_dump(), f, indent=4)
            return True
        return False
    
    def app_diff(self):
        # Compare apps
        output = {}
        # _apps = [app for app in self.apps]
        if not self.app_id_mapping: return output
        
        for app in self.apps:
            # Check if app exists in destination tenant
            _key = app['displayName']+"::"+app['appId']
            output[_key] = {}
            _temp_app = {}
            appId = app.get('appId')
            for k,v in app.items():
                if k in ['id', 'appId', 'createdDateTime', 'deletedDateTime']:
                    continue
                _temp_app[k] = v
            # Drop specific key:values
            # app.pop('id', None)
            # app.pop('appId', None)
            # app.pop('createdDateTime', None)
            # app.pop('deletedDateTime', None)
            
            if appId and appId in self.app_id_mapping:
                for dest in self.app_id_mapping.get(appId):
                    output[_key]["destination::"+dest] = dict_diff(_temp_app, self.app_id_mapping[appId][dest].get('data', {}))
            else:
                output[_key]["destination::"] = "No AppId Match. App not migrated."
                
        return output

    def sp_diff(self):
        # Compare apps
        output = {}
        # _apps = [app for app in self.apps]
        if not self.sp_id_mapping: return output
        
        for app in self.service_principals:
            # Check if app exists in destination tenant
            _key = app['displayName']+"::"+app['appId']
            output[_key] = {}
            _temp_app = {}
            appId = app.get('appId')
            for k,v in app.items():
                if k in ['id', 'appId', 'createdDateTime', 'deletedDateTime']:
                    continue
                _temp_app[k] = v
            # Drop specific key:values
            # app.pop('id', None)
            # app.pop('appId', None)
            # app.pop('createdDateTime', None)
            # app.pop('deletedDateTime', None)
            
            if appId and appId in self.sp_id_mapping:
                for dest in self.sp_id_mapping.get(appId):
                    output[_key]["destination::"+dest] = dict_diff(_temp_app, self.sp_id_mapping[appId][dest].get('data', {}))
            else:
                output[_key]["destination::"] = "No AppId Match. App not migrated."
                
        return output

# Define the database tables
class SearchTemplates(database.DatabaseMongoBaseModel):
    name: str = Field(..., description="The name of the template")
    
    app_type: Literal['servicePrincipals', 'applications'] = Field('applications', description="The type of apps to search for")
    field_search: Optional[str] = Field(None, description="Search field 'search'.")
    field_filter: Optional[str] = Field(None, description="Search field 'filter'.")
    field_raw: Optional[str] = Field(None, description="Search field 'raw'.")
    field_skip_publishers: Optional[List[str]] = Field([], description="Search field 'skip_publishers'.")
        
    
    class Settings:
        name = "ms_entra_migration_search_templates"
        title = "Application Search Templates"
        
    class Config:
        # Required for database references
        json_schema_extra = {
            "collection_name": "ms_entra_migration_search_templates",
            "type": "database_ref",
            "display_field": "{name}"
        }
