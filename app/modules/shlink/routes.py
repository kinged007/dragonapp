from fastapi import APIRouter, Query, Request, Depends, Path, Body, BackgroundTasks, status
# from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger as log
import re
from pymongo.errors import PyMongoError
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

# Import Permission checking function
# Accepts Enum object (eg. Permissions.read), string (eg. "read"), or list (eg. [Permissions.read, Permissions.write])

# Helpers
# from utils.mongo import MongoUtil
# import traceback # DEBUG

# Import module config
from .schemas import ShortLinkRequest, ShlinkDomainPostPatch, ShortLinkRedirect, ShlinkDomainDocument, ShlinkAnalyticsDocument, ShlinkShortLinkDocument
from core.utils.random import create_random_key

from core import Module
from core.config import settings
# from core.utils.task_manager import TaskManager, Retry
import asyncio

# from .tasks import process_short_link_visit
from core.utils.cache import SimpleCache

# Load router and define permissions at module level if required.
router = APIRouter() #dependencies=[Depends(verify_permissions(Module.permission(PermissionsOptions.read)))])

from core.utils.endpoints import CRUDJsonEndpoints

shlink_cache = SimpleCache()

# CRUDJsonEndpoints(
#     router = router,
#     prefix = "/testinnnnnnnnnnnnnnnnnnnngggg",
#     name_singluar="sample",
#     name_plural="samples",
#     method = ["GET","PATCH"],
#     collection = ShlinkDomainDocument,
#     description = "Sample of a GET endpoint",
#     # input_model=DomainRequest,
#     # output_model=DomainRequest,
# )


# TODO Add a get method with RedirectResponse, tracking gif?
@router.post("/visit", response_model=ShortLinkRedirect, dependencies=[]) 
async def redirect_short_link(request: Request, background_tasks: BackgroundTasks, data: dict = Body(...)):
    """
    This is a POST method to be used with redirecting scripts on a server. 
    """
    shlink_data = {}
    
    data = data.get('data') if data.get('data') else data
    shlink_data['useragent'] = data.get("HTTP_USER_AGENT","")
    shlink_data['referrer'] = data.get("HTTP_REFERER","")
    shlink_data['ip'] = data.get("REMOTE_ADDR","")
    shlink_data['request_uri'] = data.get("REQUEST_URI","")
    shlink_data['server'] = data.get("SERVER_NAME", "") # Should match the domain?
    shlink_data['server_software'] = data.get("SERVER_SOFTWARE","")
    shlink_data['language'] = data.get("HTTP_ACCEPT_LANGUAGE","")
    if shlink_data['language']: shlink_data['language'] = shlink_data['language'].split(",")[0]
        
    shlink_data['_request'] = shlink_data['request_uri'].strip("/").split("?")
    shlink_data['short_id'] = shlink_data['_request'][0]
    shlink_data['query'] = shlink_data['_request'][1] if len(shlink_data['_request']) > 1 else ""
    
    log.info("Redirecting short link: " + str(shlink_data['request_uri']))
    # print(short_id, query)
    
    try:
        
        if shlink_cache.get(shlink_data['request_uri']):
            # Record the visitor and return the cached json
            response = shlink_cache.get(shlink_data['request_uri'])
            log.debug("Getting cached result.")
        else:
            items = await ShlinkShortLinkDocument.find_one({"short_id":shlink_data['short_id']}) 
            if not items:
                # TODO if no item found, get fallback url for given domain
                # TODO Redirect to the original URL or device-specific URL if applicable, considering the domain
                
                return JSONResponse(status_code=404, content={"message": "Short link not found or is not active."})
            
            if shlink_data['server'].lower() != items.domain.lower():
                log.warning(f"Server name does not match domain: {shlink_data['server']} != {items.domain}")
                
            url = str(items.url)
            
            if items.forward_query_params:
                url += f"?{shlink_data['query']}" if "?" not in url else f"&{shlink_data['query']}"

            response = ShortLinkRedirect( url=url, response_code= 302 )
            
        
        try:
            
            # Send location finding function to background
            try:
                # background_tasks.add_task(process_short_link_visit, shlink_data)
                log.warning("TODO: Add background task to process analytics.")
            except Exception as e:
                log.error(e)
                
        except Exception as e:
            log.error(e)
            
        
        # print(items)
        
        shlink_cache.set(shlink_data['request_uri'], response)
        
        return response
        
    except Exception as e:
        log.error(e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Something went wrong. Please see the logs."})

    

def create_new_link_hook(query, output: ShlinkShortLinkDocument):
    # Generate a short link if not one specified
    # Check if the domain is valid and active
    # If valid, insert the short link into the database
    # Return the short link
    # print(query, output)
    # print(query.method)
    
    if query.method.upper() == "POST":
        # Check if domain is valid
        # domain = await ShlinkDomainDocument.find_one({"domain": output.get("domain")})
        # if no short id, generate one
        if not output.short_id:
            output.short_id = create_random_key(6)
        # if not domain, use default
        # ...
        # generate short link
        if not output.short_url:
            output.short_url = f"https://{output.domain}/{output.short_id}"
        # print(output)
        # return None
    return output


endpoints = CRUDJsonEndpoints(
    router = router,
    prefix = "/admin",
    method = ["GET","POST","PATCH","DELETE"],
    dependencies=[],
    include_in_schema=settings.DEBUG,
)

endpoints.build(
    name_singluar="domain",
    name_plural="domains",
    description = "Get 'domains' registered in the system",
    collection = ShlinkDomainDocument,
    input_model=ShlinkDomainPostPatch,
    tags=["Shlink Domains"],
)

endpoints.build(
    name_singluar="link",
    name_plural="links",
    collection = ShlinkShortLinkDocument,
    description = "Get 'links' registered in the system",
    input_hook=create_new_link_hook, 
    tags=["Shlink Links"],
)

endpoints.build(
    name_singluar="analytics",
    name_plural="analytics",
    method = ["GET","POST"],
    collection = ShlinkAnalyticsDocument,
    description = "Get 'analytics' for short links in the system",
    process_in_background=True,
    tags=["Shlink Analytics"],
)