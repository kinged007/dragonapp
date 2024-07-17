from bson import ObjectId   
from loguru import logger as log
import requests, asyncio
import os, json, httpx
from rq import get_current_job, requeue_job, Retry
from datetime import timedelta
from .main import Module
from .schemas import ShlinkAnalyticsDocument, ShortLinkVisitLocation, ShlinkShortLinkDocument, ShortLinkVisitsSummary
from core.utils.task_manager import TaskManager

os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'


botIdentifiers = [
    'bot',
    'crawl',
    'slurp',
    'spider',
    'mediapartners',
    'googlebot',
    'yahoo',
    'bingbot',
    'headless',
]

def tasks_loop_manager( func: str, *args, **kwargs ):
    
    # We run this task asyncronously because we have to interact with the database.
    loop = asyncio.new_event_loop() 
    asyncio.set_event_loop(loop)

    try:
        if func == "task_visit_location" or func == "all":
            loop.run_until_complete(task_visit_location(*args, **kwargs))


    finally:
        loop.close()
        

async def get_location_from_ip(ip_address):
    # Get module config
    module = Module()
    ipinfo_token = module.config_get("ipinfo_token",None)
    url = f"https://ipinfo.io/{ip_address}/json"
    if ipinfo_token:
        url += f"?token={ipinfo_token}"
        log.debug("Using IPInfo token")
    # Try 5 times
    async with httpx.AsyncClient() as client:
        for i in range(5):
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return response
                # response = requests.get(url)
                # if response.status_code == 200:
                    # return response
            except Exception as e:
                log.error(e)
                await asyncio.sleep(15)
    return None
    # data = response.json()
    # Use httpx to make the request
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(f"https://ipinfo.io/{ip_address}/json")
    return response

def get_country_list():
    with open(os.path.join(os.path.dirname(__file__), "src", "country_list.json"), "r") as f:
        return json.load(f)



async def process_short_link_visit(shlink_data: dict):
    """
    Process the visit data for the short link
    """
    try:
        log.info("Processing short link visit in background..." + str(shlink_data['short_id']))
        
        shlink = await ShlinkShortLinkDocument.find_one({"short_id":shlink_data['short_id']}) 
        if not shlink:
            # Oops?
            return None
        
        # Increment the click count
        shlink.visits_count += 1
        if not shlink.visits_summary:
            shlink.visits_summary = ShortLinkVisitsSummary()
            
        await shlink.save()
        
        try:
            # Insert analytics
            analytics = ShlinkAnalyticsDocument(
                short_id=shlink_data['short_id'],
                user_agent=shlink_data['useragent'],
                ip_address=shlink_data['ip'],
                referrer=shlink_data['referrer'],
                visit_location=None,
                language=shlink_data['language'],
                server_data={
                    "server_name": shlink_data['server'],
                    "server_software": shlink_data['server_software'],
                    "query": shlink_data['query'],
                    "request_uri": shlink_data['request_uri'],
                }
            )
            
            await analytics.save()
            visit_id = analytics.id
            
            if not visit_id:
                log.error("Error saving visitor stats.")
                return False
                
            log.debug("Analyzing visit: " + str(visit_id) )
            
            # item = await ShlinkAnalyticsDocument.find_one({"_id": ObjectId(visit_id)})
            # print(item)

            # Determine potential bot
            if any(x in analytics.user_agent.lower() for x in botIdentifiers):
                analytics.potential_bot = True
                log.debug(f"Visit {visit_id} is a potential bot")
            
            # Determine visitor location
            if not analytics.visit_location:
                # Update the location
                analytics.visit_location = ShortLinkVisitLocation()
                location = await get_location_from_ip(analytics.ip_address)
                if not location:
                    # Tried so many times. Will try again later.
                    log.debug("Re-queueing task to get location for " + str(analytics.id)) 
                    TaskManager.enqueue_in(timedelta(days=5), tasks_loop_manager, 'task_visit_location', str(analytics.id), retry=Retry(max=5, interval=[60*60*24, 60*60*24*7, 60*60*24*14]))
                # if location.status_code == 200:
                else:
                    location = location.json()
                    countries = get_country_list()
                    loc = location.get("loc", "").split(",")
                    analytics.visit_location.cityName = location.get("city", "")
                    analytics.visit_location.countryCode = location.get("country", "")
                    analytics.visit_location.countryName = countries[analytics.visit_location.countryCode.lower()] if analytics.visit_location.countryCode.lower() in countries else "Other"
                    analytics.visit_location.regionName = location.get("region", "")
                    analytics.visit_location.latitude = loc[0] if loc else ""
                    analytics.visit_location.longitude = loc[1] if loc else ""
                    analytics.visit_location.timezone = location.get("timezone", "")
                    analytics.visit_location.isEmpty = False
                # else:
                #     raise Exception(f"Error getting location for {analytics.ip_address}")
                
            # Finished?
            # print(visit_object)
            # Update the item
            await analytics.save()
            shlink.visits_summary.bots += 1 if analytics.potential_bot else 0
            shlink.visits_summary.non_bots += 1 if not analytics.potential_bot else 0
            shlink.visits_summary.total += 1
            await shlink.save()
                        
        except Exception as e:
            log.error(e)
        
    except Exception as e:
        log.error(e)



async def task_visit_location( visit_id: str ):
    
    # Initialize the beanie database
    if TaskManager.running_from_worker:
        await TaskManager.init_beanie([ShlinkAnalyticsDocument])
    
    analytics = await ShlinkAnalyticsDocument.find_one({"_id": ObjectId(visit_id)})
    # Determine visitor location
    if analytics:
        
        if not analytics.ip_address:
            log.error("No IP address for visit: " + str(visit_id) )
            return False
        
        # Update the location
        if not analytics.visit_location: analytics.visit_location = ShortLinkVisitLocation()
        
        location = await get_location_from_ip(analytics.ip_address)
        if not location:
            # Tried so many times. Will try again later.
            raise Exception("Error getting location for " + analytics.ip_address)
        # if location.status_code == 200:
        else:
            location = location.json()
            countries = get_country_list()
            loc = location.get("loc", "").split(",")
            analytics.visit_location.cityName = location.get("city", "")
            analytics.visit_location.countryCode = location.get("country", "")
            analytics.visit_location.countryName = countries[analytics.visit_location.countryCode.lower()] if analytics.visit_location.countryCode.lower() in countries else "Other"
            analytics.visit_location.regionName = location.get("region", "")
            analytics.visit_location.latitude = loc[0] if loc else ""
            analytics.visit_location.longitude = loc[1] if loc else ""
            analytics.visit_location.timezone = location.get("timezone", "")
            analytics.visit_location.isEmpty = False
            # Update the item
            await analytics.save()
