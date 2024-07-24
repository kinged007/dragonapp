
import msal
import asyncio

from .utils import server_request
import time, datetime
from dateutil.parser import parse
from core.utils.database import Database, ObjectId
from core.common import log, print
from core.utils.dict import dict_walk

from ..schema import Tenant, MigrationJob, Status, AppsType
from ..models.applications import ApplicationModel
from ..models.service_principals import ServicePrincipalModel

def connect_tenant(tenant_data: dict):

    try:
    
        tenant = Tenant(**tenant_data)
        # console.print(tenant) # DEBUG

        access_token = get_access_token(dict(tenant.model_dump()))

        if not access_token:
            return False

        tenant.access_token = access_token
        return tenant
    
    except Exception as e:
        log.error(f"Failed to get tenant: {e}")
        raise Exception(e)
        # return None

def tenant_request(endpoint, method="GET", data=None, headers=None, params=None, api_key=None, host = None):
    req = server_request(endpoint, method=method, data=data, headers=headers, params=params, api_key=api_key, host=host)
    # print(req)
    # print(req.headers)
    if req and req.status_code == 200:
        return req.json()
    # print(req.status_code, req.text)
    raise Exception(f"Failed to get data from tenant: {req.status_code} {req.text}")
    # log.error(f"Failed to get data from tenant: {req.status_code} {req.text}")
    # raise Exception(f"Failed to get data from tenant: {req.status_code} {req.text}")
    # return None

def get_access_token(config:dict):
    source_app = msal.ConfidentialClientApplication(
        config["client_id"],
        authority=config.get("authority"),  # For Entra ID or External ID,
        # oidc_authority=config.get("oidc_authority"),  # For External ID with custom domain
        client_credential=config["secret"],
        # token_cache=...  # Default cache is in memory only.
                        # You can learn how to use SerializableTokenCache from
                        # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
        )
    # The pattern to acquire a token looks like this.
    result = None
    # Firstly, looks up a token from cache
    # Since we are looking for token for the current app, NOT for an end user,
    # notice we give account parameter as None.
    result = source_app.acquire_token_silent(config["scope"], account=None)

    if not result:
        result = source_app.acquire_token_for_client(scopes=config["scope"])

    if "access_token" in result:
        return result['access_token']

    return None


def count_apps( params: dict = {}, baseurl: str = "https://graph.microsoft.com", access_token: str = None):
    if '$search' in params: params["$search"] = params["$search"] if params["$search"].startswith("'") or params["$search"].startswith('"') else f'"{params["$search"]}"'
    # if not params['$search']: params.pop('$search')
    
    _count = tenant_request("/v1.0/applications/$count" , 
        headers={"ConsistencyLevel": "eventual"}, 
        params=params, 
        api_key=access_token, 
        host=baseurl.replace("/v1.0", "")
    )
    return _count


def get_apps(params: dict = {}, baseurl: str = "https://graph.microsoft.com", access_token: str = None, max_results: int = 999):
    if '$search' in params: params["$search"] = params["$search"] if params["$search"].startswith("'") or params["$search"].startswith('"') else f'"{params["$search"]}"'
    # if not params['$search']: params.pop('$search')
    
    count = count_apps(params, baseurl, access_token)
    params["$top"] = max_results
    endpoint = baseurl.replace("/v1.0","").strip('/') + "/v1.0/applications"
    graph_data = []
    skip = 0
    # _progress_bar = st.progress(skip/count, text="Fetching data...")
    
    for i in range(0, count, max_results):
        
        data = tenant_request( endpoint, 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=access_token, 
        )
        # st.write(params)
        # st.json(data)
        if data:
            graph_data.extend(data["value"])
            # _progress_bar.progress(skip/st.session_state[f'{_query_key}_total'], text="Fetching data...")
            if "@odata.nextLink" in data:
                skip += max_results
                params = {}
                endpoint = data["@odata.nextLink"]
            else:
                break
        else:
            break
        time.sleep(1)
    return graph_data

def count_service_principals( params: dict = {}, baseurl: str = "https://graph.microsoft.com", access_token: str = None):
    if '$search' in params: params["$search"] = params["$search"] if params["$search"].startswith("'") or params["$search"].startswith('"') else f'"{params["$search"]}"'
    # if not params['$search']: params.pop('$search')
    
    _count = tenant_request("/v1.0/servicePrincipals/$count" , 
        headers={"ConsistencyLevel": "eventual"}, 
        params=params, 
        api_key=access_token, 
        host=baseurl.replace("/v1.0", "")
    )
    return _count


def get_service_principals(params: dict = {}, baseurl: str = "https://graph.microsoft.com", access_token: str = None, max_results: int = 999):
    if '$search' in params: params["$search"] = params["$search"] if params["$search"].startswith("'") or params["$search"].startswith('"') else f'"{params["$search"]}"'
    # if not params['$search']: params.pop('$search')
    
    count = count_service_principals(params, baseurl, access_token)
    params["$top"] = max_results
    endpoint = baseurl.replace("/v1.0","").strip('/') + "/v1.0/servicePrincipals"
    graph_data = []
    skip = 0
    # _progress_bar = st.progress(skip/count, text="Fetching data...")
    
    for i in range(0, count, max_results):
        
        data = tenant_request( endpoint, 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=access_token, 
        )
        # st.write(params)
        # st.json(data)
        if data:
            graph_data.extend(data["value"])
            # _progress_bar.progress(skip/st.session_state[f'{_query_key}_total'], text="Fetching data...")
            if "@odata.nextLink" in data:
                skip += max_results
                params = {}
                endpoint = data["@odata.nextLink"]
            else:
                break
        else:
            break
        time.sleep(1)
    return graph_data



def list_items(endpoint: str , params: dict = {}, access_token: str = None, max_results: int = 999, total_results:int = None):
    
    if not total_results:
        total_results = tenant_request(f"{endpoint.rstrip('/')}/$count" , 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=access_token, 
        )
    params["$top"] = max_results
    graph_data = []
    skip = 0

    for i in range(0, total_results, max_results):
        
        data = tenant_request( endpoint, 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=access_token, 
        )
        if data:
            graph_data.extend(data.get("value", data))
            # _progress_bar.progress(skip/st.session_state[f'{_query_key}_total'], text="Fetching data...")
            if "@odata.nextLink" in data:
                skip += max_results
                params = {}
                endpoint = data["@odata.nextLink"]

            else:
                break
        else:
            break
        time.sleep(1)
    return graph_data

def fetch_listing(option:str, endpoint:str, tenant:Tenant, query:dict = {}):
    
    # if using_saved_query:
    #     last_search = using_saved_query.get('$search', "")
    #     last_filter = using_saved_query.get('$filter', "")
    #     last_raw_params = "&".join([f"{k}={v}" for k,v in using_saved_query.items() if k not in ['$search', '$filter']])
    #     last_skip_apps_without_credentials = using_saved_query.get('skip_apps_without_credentials', "")
    # else:
    #     last_search = ""
    #     last_filter = ""
    #     last_raw_params = ""
    #     last_skip_apps_without_credentials = ""
    
    # last_skip_publishers = []
    
    # table_columns = ['id', 'displayName', 'createdDateTime', 'appId']

    skip = 0
    top = 1
    skip_apps_without_credentials = False

    if 'search' in query and query['search']: query['search'] = query['search'] if query['search'].startswith("'") or query['search'].startswith('"') else f'"{query["search"]}"'
    # last_search = query['search']
    last_filter = query['filter'] if 'filter' in query else ""
    # last_raw_params = query['raw_params']
    # last_skip_publishers = query['skip_publishers'] if 'skip_publishers' in query else []

    params = {}
    try:
        _q = 'search'
        if 'search' in query and query['search']: params['$search'] = query['search']
        _q = 'filter'
        if 'filter' in query and query['filter']: params['$filter'] = query['filter']
        _q = 'raw_params'
        if 'raw_params' in query and query['raw_params']:
            _raw_params = query['raw_params'].split("&")
            params.update({i.split("=")[0]:i.split("=")[1] for i in _raw_params})
        _q = 'skip_publishers'
        if 'skip_publishers' in query and query['skip_publishers']:
            _pubs = ",".join([f"'{s}'" if s else f"null" for s in query['skip_publishers']])
            params['$filter'] = f"{last_filter+' and ' if last_filter else ''}NOT(publisherName in ({_pubs}))"
            params['$count'] = "true"
        _q = 'skip_apps_without_credentials'
        if 'skip_apps_without_credentials' in query and query['skip_apps_without_credentials']:
            # params['$filter'] = f"{params.get('$filter','')} and (passwordCredentials/any(x: x/endDateTime ge now() or x/endDateTime eq null))"
            skip_apps_without_credentials = True
    except Exception as e:
        raise Exception(f"Failed to parse query '{_q}': {e}")
        
    endpoint_url = f"{tenant.endpoint.strip('/')}/beta/{endpoint.strip('/')}"
    
    # console.print(params)
    
    try:
        count = tenant_request(f"{endpoint_url}/$count" , 
            headers={"ConsistencyLevel": "eventual"}, 
            params=params, 
            api_key=tenant.access_token, 
            # host=tenant.endpoint
        )
        if not count:
            raise Exception(False)
        
        # console.print(f"Total {option} that match search criteria (pre processing): {count}", style="bold magenta")
    
    except Exception as e:
        # continue
        if str(e) == "False":
            count = 99999
        else:
            # console.print(f"Failed to fetch {option}: {e}", style="bold red")
            log.error(f"Failed to fetch {option}: {e}")
            log.error(params)
            raise Exception(f"Failed to fetch {option}: {e}")
            # return []
        pass
        
    try:
        list_of_items = list_items(endpoint_url, params=params, access_token=tenant.access_token, total_results=count, max_results=999)
        today = datetime.datetime.now(tz=datetime.timezone.utc)  #+ datetime.timedelta(days=1) # UTC time
        for i, item in enumerate(list_of_items):
            if item.get('passwordCredentials'):
                list_of_items[i]['passwordCredentials'] = [x for x in item['passwordCredentials'] if not x.get('endDateTime') or parse(x.get('endDateTime')) > today]
            if item.get('keyCredentials'):
                list_of_items[i]['keyCredentials'] = [x for x in item['keyCredentials'] if not x.get('endDateTime') or parse(x.get('endDateTime')) > today]
            # list_of_items = [i for i in list_of_items if not i.get('passwordCredentials') or any([not x.get('endDateTime') or parse(x.get('endDateTime')) > today for x in i.get('passwordCredentials')])]
            # console.print(f"Found {count-len(list_of_items)} expired apps. Skipping", style="bold magenta")
        if skip_apps_without_credentials:
            list_of_items = [i for i in list_of_items if i.get('passwordCredentials') or i.get('keyCredentials')]
            # console.print(f"Skipping {count-len(list_of_items)} apps without credentials.", style="bold magenta")
            
    except Exception as e:
        # console.print(f"Failed to fetch {option}: {e}", style="bold red")
        log.error(f"No {option} found for this search criteria")
    
    if not list_of_items:
        # console.print(f"No {option} found for this search criteria", style="bold red")
        log.error(f"No {option} found for this search criteria")
    
    return list_of_items
    


async def post_process_migration_job(job: MigrationJob):
    """
    Post processing of migration job.
    """
    
    job.status = Status.IN_PROGRESS
    apps = job.apps if job.apps_type == AppsType.applications else job.service_principals
    
    # console.rule("Post Processing Migration Job", style="bold magenta")
    # For completed jobs, create credentials
    if job.apps_type == AppsType.applications:
        pass
        # print(job.apps)
        # # Cannot add more than 1 password(s) for create application. Skip passwordCredentials and keyCredentials and add them later.
        # if hasattr(old_app, 'passwordCredentials'): delattr(old_app, 'passwordCredentials')
        # if hasattr(old_app, 'keyCredentials'): delattr(old_app, 'keyCredentials')
        # # identifierUris with api://<appId> should refer to its new appId.
        # if hasattr(old_app, 'identifierUris'): old_app.identifierUris = [x for x in old_app.identifierUris if not x.startswith("api://")]
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

        today = datetime.datetime.now(tz=datetime.timezone.utc)  #+ datetime.timedelta(days=1) # UTC time

        for i in range(len(apps)):
            try:
                # console.print(apps[i])
                if job.apps_type == AppsType.applications:
                    old_app = ApplicationModel(**apps[i])
                if job.apps_type == AppsType.servicePrincipals:
                    old_app = ServicePrincipalModel(**apps[i])
                # console.print(old_app.post_model())
                
            except Exception as e: 
                yield f"❌ Failed to parse app data for {apps[i].get('displayName','?')}: {e}"
                continue
            
        
            # Check if app is already migrated.
            if not job.app_id_mapping.get(old_app.appId, {}).get(dest_tenant.client_id):
                yield f"❌ App '{old_app.displayName}' NOT migrated to {dest.name}"
                continue
            
            if job.migration_options.new_app_suffix: # TODO Change to use template, ... NOTE not really fundamental, only for logging 
                old_app.displayName += " " + job.migration_options.new_app_suffix
                
            yield f"Post processing app '{old_app.displayName}' on {dest.name}"

            endpoint = dest_tenant.endpoint.replace("/v1.0","").strip('/') + "/v1.0/"
            endpoint += str(job.apps_type.value)
            
            new_app = job.app_id_mapping[old_app.appId][dest_tenant.client_id]['data'] if job.apps_type == AppsType.applications else job.sp_id_mapping[old_app.appId][dest_tenant.client_id]['data']

            # execute creation
            try:
                
                if not old_app.appId:
                    raise Exception(f"App '{old_app.displayName}' does not have an appId.")
                
                if not new_app:
                    raise Exception(f"App '{old_app.displayName}' does not have a new app Id.")
                
                ####### passwordCredentials
                
                try:
                    if hasattr(old_app, 'passwordCredentials'): 
                        # Create new passwordCredentials
                        if old_app.passwordCredentials:
                            _passwords = [x for x in old_app.passwordCredentials if not x.endDateTime or parse(x.endDateTime) > today]
                            # if not _passwords and job.migration_options.generate_new_password_if_all_expired:
                            #     # Generate new password
                            #     _passwords = old_app.passwordCredentials[0] if old_app.passwordCredentials else []
                            for password in _passwords:
                                # Create password
                                _display_name = password.displayName if password.displayName else "New Migration Password"
                                # Check if password exists or created already
                                if any([x for x in new_app.get('passwordCredentials',[]) if x.get('displayName') == _display_name]):
                                    yield f"Password '{_display_name}' already exists..."
                                    continue
                                # Create new password
                                req = server_request(
                                    endpoint + f"/{new_app['id']}/addPassword", 
                                    method="POST", 
                                    data={
                                        "passwordCredential": {
                                            "displayName": _display_name,
                                        }
                                    }, 
                                    api_key=dest_tenant.access_token, 
                                    # host=dest_config.endpoint
                                )
                                if req and req.status_code == 200:
                                    yield f"✅ Password created successfully: {_display_name}"
                                    if 'passwordCredentials' not in new_app:
                                        new_app['passwordCredentials'] = []
                                    new_app['passwordCredentials'].append(req.json())
                                else:
                                    yield f"❌ Failed to create password: {_display_name}: " + str(req.text)
                except Exception as e:
                    log.error(f"Failed to create passwordCredentials: {e}")
                    raise Exception(f"Failed to create passwordCredentials: {e}")
                
                ####### keyCredentials
                
                # if hasattr(old_app, 'keyCredentials'): # TODO post process keyCredentials
                
                ####### identifierUris
                
                try:
                    # identifierUris with api://<appId> should refer to its new appId.
                    if hasattr(old_app, 'identifierUris'): 
                        # TODO Fetch existing identifierUris to ensure no URI is overwritten by accident!
                        _existing_uris = []
                        _existing_uris_req = server_request(
                            endpoint + f"/{new_app['id']}", 
                            method="GET", 
                            params={
                                "$select": "identifierUris"
                            },
                            api_key=dest_tenant.access_token, 
                        )
                        if _existing_uris_req and _existing_uris_req.status_code == 200:
                            _existing_uris = _existing_uris_req.json()
                            _existing_uris = _existing_uris.get('identifierUris', [])
                        else:
                            yield f"Failed to get existing identifierUris: " + str(_existing_uris_req.text)
                            # TODO COntinue??
                            
                        identifierUris = [x for x in old_app.identifierUris ] # All URI's
                        _update_uris = []
                        
                        for uri in identifierUris:
                            # Get format: https://learn.microsoft.com/en-us/entra/identity-platform/security-best-practices-for-app-registration#application-id-uri 
                            # # TODO May received tenant related URI's. May need to replace with new app/tenant ids.    
                            _new_uri = None
                            if uri == "api://" + old_app.appId:
                                _new_uri = "api://" + new_app['appId'] 
                            
                            if _new_uri and _new_uri not in _existing_uris: #if _new_uri not in new_app.get('identifierUris', []):
                                _update_uris.append(_new_uri)
                        
                        if _update_uris:
                            req = server_request(
                                endpoint + f"/{new_app['id']}", 
                                method="PATCH", 
                                data={
                                    "identifierUris": _update_uris # includes existing URIs to avoid overwriting existing ones.
                                }, 
                                api_key=dest_tenant.access_token, 
                            )
                            if req and req.status_code == 204:
                                yield f"✅ identifierUris updated successfully"
                                if 'identifierUris' not in new_app:
                                    new_app['identifierUris'] = []
                                new_app['identifierUris'] = _update_uris
                            else:
                                yield f"❌ Failed to update identifierUris: " + str(req.text)
                except Exception as e:
                    log.error(f"Failed to update identifierUris: {e}")
                    raise Exception(f"Failed to update identifierUris: {e}")
                
                #### servicePrincipal: servicePrincipalNames
                
                try: 
                    if hasattr(old_app, 'servicePrincipalNames'): 
                        # Recreate servicePrincipalNames after creation.
                        print("OLD APP", type(old_app), old_app)
                        print("NEW APP", type(new_app), new_app)
                        
                        _existing_uris = []
                        _existing_uris_req = server_request(
                            endpoint + f"/{new_app['id']}", 
                            method="GET", 
                            params={
                                "$select": "servicePrincipalNames"
                            },
                            api_key=dest_tenant.access_token, 
                        )
                        if _existing_uris_req and _existing_uris_req.status_code == 200:
                            _existing_uris = _existing_uris_req.json()
                            _existing_uris = _existing_uris.get('servicePrincipalNames', [])
                        else:
                            yield f"Failed to get existing servicePrincipalNames: " + str(_existing_uris_req.text)
                            # TODO COntinue??
                            
                        servicePrincipalNames = [x for x in old_app.servicePrincipalNames ] # All URI's
                        _update_uris = []
                        
                        for uri in servicePrincipalNames:
                            # Get format: https://learn.microsoft.com/en-us/entra/identity-platform/security-best-practices-for-app-registration#application-id-uri 
                            # # TODO May received tenant related URI's. May need to replace with new app/tenant ids.    
                            _new_uri = None
                            if uri == "api://" + old_app.appId:
                                _new_uri = "api://" + new_app['appId'] 
                            
                            if _new_uri and _new_uri not in _existing_uris: #if _new_uri not in new_app.get('servicePrincipalNames', []):
                                _update_uris.append(_new_uri)
                        
                        print(_update_uris)
                        
                        if _update_uris:
                            req = server_request(
                                endpoint + f"/{new_app['id']}", 
                                method="PATCH", 
                                data={
                                    "servicePrincipalNames": _update_uris # includes existing URIs to avoid overwriting existing ones.
                                }, 
                                api_key=dest_tenant.access_token, 
                            )
                            if req and req.status_code == 204:
                                yield f"✅ servicePrincipalNames updated successfully"
                                if 'servicePrincipalNames' not in new_app:
                                    new_app['servicePrincipalNames'] = []
                                new_app['servicePrincipalNames'] = _update_uris
                            else:
                                yield f"❌ Failed to update servicePrincipalNames: " + str(req.text)
                except Exception as e:
                    log.error(f"Failed to update servicePrincipalNames: {e}")
                    raise Exception(f"Failed to update servicePrincipalNames: {e}")
                
                # Update app_id_mapping
                job.app_id_mapping[old_app.appId][dest_tenant.client_id]['data'] = new_app

            except Exception as e:
                    # Store failed attempt in migration job
                    # Check if req has been defined
                    yield f"❌ Failed to post process app '{old_app.displayName}' on '{dest.name}':\n {e}"
            
            yield "Post Processing Complete"
            job.status = Status.COMPLETED

            
            await asyncio.sleep(1)

                
                
                
async def process_migration_job(job: MigrationJob):
    """
    Processes the migration job by migrating apps to destination tenants.
    
    Notes:
        - Migration additional confirmation steps/approvals.
        - Ignore expired apps/credentials. - parse date fields.
        - Create NEW secrets and keys!!!
        - return client id, secret, and openid-configuration.
        - future feature: keep track of expiring secrets/certificates + generate new secrets.
        - NOTE: identifierUris may contain custom domain names and formats. eg:
            sandoz-sb.identifynow.com/sp
            e11.chbs.cvpn.nova.com/saml-vpn/...
            api://simeoncloud/<app-id>
            urn:p2p_cert
            urn:microsoft:adfs:claims:upn
            urn:amazon:cognito
            ni3q4NI23fAs - ????
            Test-Application-SAML
            name:sp:TEST:ssoParticipant.uat...
        ---- All ok to copy as is. Check for app/tenant ids and replace with new ones. Other URIs may be custom and copied directly.
        
        - REVIEW
            migrate/onboard? apps - 
            naming conventions  - enforce preagreed naming/formats - examples?
            assignment group... salepoint, request, receive access.... assign predefined group to app.
            - access profile
            
            
            KEY POINTS:
                - GUI - modify JSON before sending/remove params, 
                - Azure AD Group assigned to new App - For SAML (Enterprise Apps) apps.
                - App Naming convention eg.
                - Integration with Sailpoint IdentityNow APIS.
                - Service Principals
                - OpenID Endpoint Urls
                - Consider how to handle onboarding of apps?
            - 1. set up saml and oauth apps for testing
            - 2. examples and variables for naming convention 
            - 3. worflow for onboarding apps etc.
        
        NOTE in SAML, there are metadata parameters like Assertion Consumer URI, EntityID (synonym for Entra identifierUris...)
        
        - Cant modify redirectUris and redirectUriSettings in the same request. Verify Settings post creation
        - Creating passwordCredentials returns password that will not be shown again, only when using addPassword method.
        # NOTE: Cannot add more than 1 password(s) for create application.
        - Using POST / PATCH to set passwordCredential is not supported. Use the addPassword and removePassword methods to update the password or secret for an application.
        - keyCredential - create/generate and apply certificates separately.https://learn.microsoft.com/en-us/graph/applications-how-to-add-certificate?tabs=http
        - to refer to the app by the appId, use /applications(appId='{appId}')
        - Values of identifierUris hostnames must be a verified domain on the tenant. Create list of filters templates to skip certain app typs (eg. VPN, etc.)
        - API Permissions are not granted by default, need to look for a way to grant permissions.
        - ISSUE: Property displayName on the service principal does not match the application object
    """
    yield f"Processing Migration Job: {job.name}"
    
    await asyncio.sleep(0.5)
    
    failures = []
    
    # if job.status != Status.APPROVED:
    #     raise Exception(f"Migration job is NOT Pending  ({job.status.value})")
    
    # Dont need Source Tenant since we already have the JSON object of apps to migrate.
    
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
        
        yield f"Connecting to {dest_tenant.name}"
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
                
            
                # Check if app is already migrated.
                if job.apps_type == AppsType.applications:
                    if job.app_id_mapping.get(_data.appId, {}).get(dest_tenant.client_id):
                        yield f"App '{_data.displayName}' already migrated to {dest_tenant.name}"
                        await asyncio.sleep(0.1)
                        continue
                if job.apps_type == AppsType.servicePrincipals:
                    if job.sp_id_mapping.get(_data.appId, {}).get(dest_tenant.client_id):
                        yield f"Service Principal '{_data.displayName}' already migrated to {dest_tenant.name}"
                        await asyncio.sleep(0.1)
                        continue

                
                # print(_data)
                yield f"Migrating app '{_data.displayName}' to {dest_tenant.name}"
                await asyncio.sleep(0.5)

                endpoint = dest_tenant.endpoint.replace("/v1.0","").strip('/') + "/v1.0/"
                endpoint += str(job.apps_type.value)
                    
                # migration code here...
                # Drop specific key:values
                if job.apps_type == AppsType.applications:
                    # Cannot add more than 1 password(s) for create application. Skip passwordCredentials and keyCredentials and add them later.
                    if hasattr(_data, 'passwordCredentials'): delattr(_data, 'passwordCredentials')
                    if hasattr(_data, 'keyCredentials'): delattr(_data, 'keyCredentials')
                    # identifierUris with api://<appId> should refer to its new appId.
                    if hasattr(_data, 'identifierUris'): 
                        # SEE Notes above
                        delattr(_data, 'identifierUris')
                        # _data.identifierUris = [x for x in _data.identifierUris if not x.startswith("api://")]
                if job.apps_type == AppsType.servicePrincipals:
                    # Walk the manifest and swap old id for the new AppId
                    old_app_id = _data.appId
                    if old_app_id in job.app_id_mapping:
                        yield "Swapping AppIds..."
                        _new_app_id = job.app_id_mapping[old_app_id][dest_tenant.client_id]['appId']
                        if not _new_app_id:
                            # raise Exception(f"Failed to get new app id for app '{_data.displayName}'") # TODO What is the fallback? ie. We are migrating an app that has not been migrated / registered.
                            yield f"❌ Failed to get new app id for app '{_data.displayName}'. App seems to not have been migrated yet."
                            continue
                        
                        _data.appId = _new_app_id
                        
                        # Walk the manifest and swap old id for the new AppId
                        def _swap_appids(key, value):
                            if isinstance(value, str):
                                if old_app_id in value:
                                    print("Swapping AppIds:", key, value, "->", value.replace(old_app_id, _new_app_id))
                                    return value.replace(old_app_id, _new_app_id)
                            elif isinstance(value, list):
                                new_values = []
                                for x in value:
                                    if old_app_id in x and isinstance(x, str):
                                        new_values.append(x.replace(old_app_id, _new_app_id))
                                        print("Swapping AppIds:", key, x, "->", x.replace(old_app_id, _new_app_id))
                                    else:
                                        new_values.append(x)
                                return new_values
                            return value
                        _new_data = dict_walk(_data.model_dump(), _swap_appids)
                        if _new_data:
                            yield "Swapping AppIds... Done"
                            _data = ServicePrincipalModel(**_new_data)
                            
                    # Drop specific key:values
                    # add them afterwards
                    if hasattr(_data, 'servicePrincipalNames'): delattr(_data, 'servicePrincipalNames') # recreate servicePrincipalNames after creation.
                    # Replace AppIds with new AppIds
                    
                        
                
                # execute creation
                try:
                    
                    if not _data.appId:
                        raise Exception(f"App '{_data.displayName}' does not have an appId.")
                    
                    if job.migration_options.new_app_suffix: # TODO use template instead
                        _data.displayName += " " + job.migration_options.new_app_suffix
                    
                    if job.migration_options.use_upsert:
                        
                        req = server_request(
                            endpoint + "(appId='{appId}')".format(appId=_data.appId), # TODO Upsert should refer to the NEW appId, not the old one!
                            method="PATCH", 
                            data=_data.post_model(), 
                            api_key=dest_tenant.access_token, 
                            # host=dest_tenant.endpoint
                        )
                        
                    else:
                        
                        req = server_request(
                            endpoint, 
                            method="POST", 
                            data=_data.post_model(), 
                            api_key=dest_tenant.access_token, 
                            # host=dest_tenant.endpoint
                        )
                    
                    if req and req.status_code == 201:
                        # Check emoji: https://emojicombos.com/
                        yield f"✅ App '{_data.displayName}' migrated successfully to {dest_tenant.name}"
                        await asyncio.sleep(0.1)
                        
                        # Store successful migration in migration job.
                        _new_app_id = req.json().get('appId')
                        if not _new_app_id:
                            raise Exception(f"Failed to get new app id for newly created app '{_data.displayName}'")

                        # Applications
                        if job.apps_type == AppsType.applications:
                            if _data.appId not in job.app_id_mapping: 
                                job.app_id_mapping[_data.appId] = {}
                            job.app_id_mapping[_data.appId].update({dest_tenant.client_id: {"appId": _new_app_id, "data": req.json() }})
                        
                        # Service Principals
                        if job.apps_type == AppsType.servicePrincipals:
                            if _data.appId not in job.sp_id_mapping:
                                job.sp_id_mapping[_data.appId] = {}
                            job.sp_id_mapping[_data.appId].update({dest_tenant.client_id: {"appId": _new_app_id, "data": req.json() }})
                
                    elif req and req.status_code == 204: # no response code for PATCH
                        yield f"✅ App '{_data.displayName}' UPDATED successfully in {dest_tenant.name}"
                        if job.apps_type == AppsType.applications:
                            if _data.appId not in job.app_id_mapping: 
                                job.app_id_mapping[_data.appId] = {}
                            job.app_id_mapping[_data.appId].update({dest_tenant.client_id: {"appId": _data.appId, "data": _data.model_dump() }})
                        if job.apps_type == AppsType.servicePrincipals:
                            if _data.appId not in job.sp_id_mapping:
                                job.sp_id_mapping[_data.appId] = {}
                            job.sp_id_mapping[_data.appId].update({dest_tenant.client_id: {"appId": _data.appId, "data": _data.model_dump() }})

                    else:
                        raise Exception()

                except Exception as e:
                        # Store failed attempt in migration job
                        # Check if req has been defined
                        _fail = {}
                        if 'req' in locals():
                            yield f"❌ Failed to migrate app '{_data.displayName}' to {dest_tenant.name}:\n RESPONSE CODE {req.status_code} {req.text}"
                            failures.append({"destination": dest_tenant.client_id, "app": _data, "response": req.text, "status": req.status_code })
                            # if dest_tenant.client_id not in job.apps_failed:
                                # job.apps_failed[_data.appId] = {}
                            # job.apps_failed[_data.appId].update({dest_tenant.client_id: {"app": _data, "response": req.json(), "status": req.status_code }})
                            _fail = {dest_tenant.client_id: {"app": _data, "response": req.json(), "status": req.status_code }}
                        else:
                            yield f"❌ Failed to migrate app '{_data.displayName}' to {dest_tenant.name}:\n {e}"
                            failures.append({"destination": dest_tenant.client_id, "app": _data, "response": str(e), "status": 500 })
                            # if dest_tenant.client_id not in job.apps_failed:
                                # job.apps_failed[_data.appId] = {}
                            # job.apps_failed[_data.appId].update({dest_tenant.client_id: {"app": _data, "response": str(e), "status": 500 }})
                            _fail = {dest_tenant.client_id: {"app": _data, "response": str(e), "status": 500 }}

                        if job.apps_type == AppsType.applications:
                            if _data.appId not in job.apps_failed: 
                                job.apps_failed[_data.appId] = {}
                            job.apps_failed[_data.appId].update({dest_tenant.client_id: {"appId": _data.appId, "data": _data.model_dump() }})
                        if job.apps_type == AppsType.servicePrincipals:
                            if _data.appId not in job.sp_failed:
                                job.sp_failed[_data.appId] = {}
                            job.sp_failed[_data.appId].update(_fail)

                        await asyncio.sleep(0.1)
                
                await asyncio.sleep(2)

                # Update progress bar
            
            if failures:
                yield f"Migration {dest_tenant.name} did not complete successfully."
            else:
                yield f"Migration {dest_tenant.name} completed successfully."
    
            await asyncio.sleep(0.1)
            
        except Exception as e:
            yield f"Failed: {dest_tenant.name} - {e}"
            failures.append({"destination": dest_tenant.client_id, "error": str(e) })
        
    if failures:
        yield f"❌ Migration failed for some apps"
        yield str(failures)
        # console.print(failures)
        job.status = Status.FAILED
    else:
        yield f"✅ Migration completed successfully"
        job.status = Status.COMPLETED

    
    
async def process_service_principal_migration(job: MigrationJob, source_tenant: Tenant):
    """
    Processing of Service Principals.
    1. Go through the apps that have been migrated, and search for corresponding Service Princicpals.
    2. Replace AppIds with the new AppIds.
    3. Migrate Service Principals to destination tenants.
    """
    
    yield "Searching for Service Principals related to migrated Apps"
    
    # Prepare tenant object
    if not source_tenant.access_token:
        source_tenant = connect_tenant(source_tenant.model_dump())
    
    if not source_tenant or not source_tenant.access_token:
        yield "Failed to connect to the source tenant!"
        job.status = Status.FAILED
        return
    
    app_ids = job.app_id_mapping.keys()
    if not app_ids: 
        yield "No apps found to migrate!"
        job.status = Status.COMPLETED
        return
    
    app_ids = [f"'{i}'" for i in app_ids]
        
    try:
        # list_of_apps = msapp.fetch_listing(migration_job.apps_type, endpoint=f"/{migration_job.apps_type}", tenant=tenant, query={
        _q = {
            # "search": _search.value, 
            "filter": f"appId in [{','.join(app_ids)}]", 
            # "raw_params": _raw.value, 
            # "skip_publishers": _skip_publishers.value if _skip_publishers and _app_type.value == 'servicePrincipals' else None, 
        }
        list_of_apps = fetch_listing(job.apps_type.value, endpoint=f"/{job.apps_type.value}", tenant=source_tenant, query=_q)
    except Exception as e:
        yield f"Failed to fetch listing: {e}"
        job.status = Status.FAILED
        return

    yield f"Found {len(list_of_apps)} {job.apps_type.value} to migrate."
    
    if list_of_apps and len(list_of_apps)>0:
        # We have SP to migrate
        job.service_principals = list_of_apps
    
    job.status = Status.COMPLETED
    
    
    