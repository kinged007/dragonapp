from loguru import logger as log

import msal
import asyncio

from .utils import server_request
import time, datetime
from dateutil.parser import parse

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
        return None

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

    if query['search']: query['search'] = query['search'] if query['search'].startswith("'") or query['search'].startswith('"') else f'"{query["search"]}"'
    last_search = query['search']
    last_filter = query['filter']
    last_raw_params = query['raw_params']
    last_skip_publishers = query['skip_publishers'] if 'skip_publishers' in query else []

    params = {}
    try:
        _q = 'search'
        if query['search']: params['$search'] = query['search']
        _q = 'filter'
        if query['filter']: params['$filter'] = query['filter']
        _q = 'raw_params'
        if query['raw_params']:
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
            dedicated group... salepoint, request, receive access.... assign predefined group to app.
            - access profile
            
            
            KEY POINTS:
                - GUI - modify JSON before sending/remove params, 
                - Azure AD Group assigned to new App - For SAML (Enterprise Apps) apps.
                - App Naming convention 
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
    """
    yield f"Processing Migration Job: {job.name}"
    
    await asyncio.sleep(0.5)
    
    failures = []
    
    if job.status != Status.APPROVED:
        raise Exception(f"Migration job is NOT Pending  ({job.status.value})")
    
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
            apps = job.apps
            job.status = Status.IN_PROGRESS

            yield f"Migrating '{len(apps)}' '{job.apps_type}' to '{dest_tenant.name}'"
            await asyncio.sleep(1)
                

            for i in range(len(apps)):
                
                try:
                    
                    yield f"Parsing app data for {apps[i].get('displayName','?')}"
                    await asyncio.sleep(0.3)
                    # console.print(apps[i])
                    if job.apps_type == AppsType.applications:
                        _data = ApplicationModel(**apps[i])
                    if job.apps_type == AppsType.servicePrincipals:
                        _data = ServicePrincipalModel(**apps[i])
                    # console.print(_data.post_model())
                    
                except Exception as e: 
                    yield f"❌ Failed to parse app data for {apps[i].get('displayName','?')}: {e}"
                    await asyncio.sleep(0.1)
                    continue
                
            
                # Check if app is already migrated.
                if job.app_id_mapping.get(_data.appId, {}).get(dest_tenant.client_id):
                    yield f"App '{_data.displayName}' already migrated to {dest_tenant.name}"
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

                    
                        
                
                # execute creation
                try:
                    
                    if not _data.appId:
                        raise Exception(f"App '{_data.displayName}' does not have an appId.")
                    
                    if job.migration_options.new_app_suffix:
                        _data.displayName += " " + job.migration_options.new_app_suffix
                    
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

                        if _data.appId not in job.app_id_mapping:
                            job.app_id_mapping[_data.appId] = {}
                        job.app_id_mapping[_data.appId].update({dest_tenant.client_id: {"appId": _new_app_id, "data": req.json() }})
                            
                    else:
                        raise Exception()

                except Exception as e:
                        # Store failed attempt in migration job
                        # Check if req has been defined
                        if 'req' in locals():
                            yield f"❌ Failed to migrate app '{_data.displayName}' to {dest_tenant.name}:\n RESPONSE CODE {req.status_code} {req.text}"
                            failures.append({"destination": dest_tenant.client_id, "app": _data, "response": req.text, "status": req.status_code })
                            if dest_tenant.client_id not in job.apps_failed:
                                job.apps_failed[_data.appId] = {}
                            job.apps_failed[_data.appId].update({dest_tenant.client_id: {"app": _data, "response": req.json(), "status": req.status_code }})
                        else:
                            yield f"❌ Failed to migrate app '{_data.displayName}' to {dest_tenant.name}:\n {e}"
                            failures.append({"destination": dest_tenant.client_id, "app": _data, "response": str(e), "status": 500 })
                            if dest_tenant.client_id not in job.apps_failed:
                                job.apps_failed[_data.appId] = {}
                            job.apps_failed[_data.appId].update({dest_tenant.client_id: {"app": _data, "response": str(e), "status": 500 }})
                        await asyncio.sleep(0.1)
                # TODO Save updated migration job
                # job.save()
                
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
        # console.print(failures)
        job.status = Status.FAILED
    else:
        yield f"✅ Migration completed successfully"
        job.status = Status.COMPLETED
        # Post Processing
        # console.print("Post Processing...", style="bold green")
        # post_process_migration_job(job)
    
    # TODO job.save()

    # TODO migration_job_report(job)