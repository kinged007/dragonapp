from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Depends, Request, BackgroundTasks, HTTPException #, Body, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
# from beanie import init_beanie, Document
# from beanie.operators import In
# from motor.motor_asyncio import AsyncIOMotorClient
from time import time, sleep
from core import log, print
from core.utils.sqlite import engine, Base
from core.schemas.database import DatabaseMongoBaseModel
import traceback
from os import path
from importlib import import_module, util
import inspect
import sys

from core.config import settings
from core import Module
from core.utils.database import Database
from pymongo import IndexModel

# TODO Use https://www.adminer.org/en/ for advanced database management ??

_start = time()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Lifespan context manager for the FastAPI application. This is where the application is initialized and cleaned up.
    Raises an error if anything goes wrong during the initialization process.
    
    General startup workflow:
        - Loaded databases are initialized
        - Configuration is loaded.
        - Routes are registered and included.
        - Cron checks are made and handlers called.
    General shutdown workflow:
        - Cron jobs are stopped.
        - Databases are closed.
        - Application is shut down.
        
    """
    # Load models and data that will be used throughout the lifespan of the app
    # eg.
    # lifespan_variables["test"] = name_of_function
    log.info("Loading lifespan function")
    # Initialize MongoDB instances
    if await start_database():
    # Initialize Module configurations and DB schemas
        await start_modules()  
    
    else:
        log.error("Failed to initialize Database. Exiting.")
        return

    log.info("Application started in {:.3f} seconds".format(time() - _start))

    yield
    # Clean up the models and data and release the resources
    Database.close()
    log.info("Lifespan shutdown")



# executed on each new incoming request
async def start_database():
    
    db_initialised = False
    _sql_db = []
    _mongo_db = []
    
    # Load databases from modules
    for mod_db in Module._databases:
        if issubclass(mod_db, DatabaseMongoBaseModel):
            _mongo_db.append(mod_db)
        if issubclass(mod_db, Base):
            _sql_db.append(mod_db)    
    
    # Load SQL databases 
    # SQLAlchemy automatically loads imported database schemas into the Base.metadata.tables dictionary.
    if Base.metadata.tables.keys() and len(list(Base.metadata.tables.keys())) > 0:
        Base.metadata.create_all(bind=engine)
        log.info("SQL Database Initialized: " + str(list(Base.metadata.tables.keys())))
    
    # Load MongoDB databases
    # Connect to MongoDB
    if not settings.MONGODB_URI:
        log.error("MONGODB_URI environment variable is not set.")
    else:
        try:
            # Use a connection pool for MongoDB and PyMongo! 
            _dbConnection = "TinyDB" if 'tinydb' in settings.MONGODB_URI else "MongoDB"
            log.info(f"Connecting to {_dbConnection} Database: {settings.DATABASE_NAME}")
            if Database.connect(settings.MONGODB_URI, settings.DATABASE_NAME):
                # collection.create_index([('field_i_want_to_index', pymongo.TEXT)], name='search_index', default_language='english')
                # https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#pymongo.collection.Collection.create_index
                # TODO Create indexes for the given collections
                if _mongo_db:
                    if not Database.using_tinydb:
                        # Loop through all the collections and create indexes
                        for collection in _mongo_db:
                            if hasattr(collection, "Settings"):
                                if hasattr(collection.Settings, "indexes"):
                                    _indexes = []
                                    if not isinstance(collection.Settings.indexes, list):
                                        collection.Settings.indexes = [collection.Settings.indexes]
                                    for index in collection.Settings.indexes:
                                        # Create the index
                                        if not isinstance(index, IndexModel):
                                            raise Exception(f"Index is not an instance of pymongo.IndexModel: {index}")
                                        _indexes.append(index)
                                    if _indexes:
                                        Database.db[collection.Settings.name].create_indexes(_indexes)
                                        log.info(f"Created index on {collection.Settings.name}")
                            else:
                                log.error(f"No Settings class found for {collection}")
                                raise Exception(f"No Settings class found for {collection}")
                        
                        log.info("MongoDB Initialized tables: " + str([t.Settings.name for t in _mongo_db]))
                
            # client = AsyncIOMotorClient(settings.MONGODB_URI)
            # # Specify the database
            # database = client[settings.DATABASE_NAME]
            # # NOTE We HAVE to import using full path to avoid issues with Beanie - why?
            # # tables_list = ['tables.api_keys.ApiKeys', 'tables.cron.CronExecutor', 'tables.config.ModuleConfig']
            # await init_beanie(database=database, document_models=_mongo_db)
            # log.info("MongoDB Initialized tables: " + str([t.Settings.name for t in _mongo_db]))
        except Exception as e:
            log.error(f"Failed to initialize {_dbConnection} '{settings.DATABASE_NAME}': {e}")
            log.error("Databases: " + str(_mongo_db))
            # return False

    db_initialised = True

    return db_initialised


async def start_modules():
    """
    Loads modules configuration and database schemas.
    """
    log.info("Lifespan: Loading Modules")
    # Load configurations for modules
    for module_name, module in Module.modules.items():
        try:
            if module:
                module.fetch_config()
                # print(__file__, module)
                log.info(f"Module '{module.name}' config loaded")
        except Exception as e:
            log.error(f"Failed to load module '{module}': {e}")
            traceback.print_exc()
            return False
    pass


from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    import sentry_sdk
    from sentry_sdk.integrations.starlette import StarletteIntegration
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.pymongo import PyMongoIntegration
    from sentry_sdk.integrations.loguru import LoguruIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration

    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN), 
        enable_tracing=True, 
        release=f"{settings.PROJECT_NAME}@{settings.APP_VERSION}",
        environment=settings.ENVIRONMENT,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        integrations=[
            StarletteIntegration(
                transaction_style="endpoint"
            ),
            FastApiIntegration(
                transaction_style="endpoint"
            ),
            PyMongoIntegration(),
            LoguruIntegration(),
            AsyncioIntegration(),


        ],

    )



app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_VERSION_STR.format(version=1)}/openapi.json",
    # openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description= settings.PROJECT_DESCRIPTION,
    summary= settings.PROJECT_SUMMARY,
    version= settings.APP_VERSION,
    lifespan=lifespan,
    # TODO Hide docs if settings.API_DOCS is False
    # include_in_schema=False,
    # docs_url=None,
    
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

"""
### General workflow

- Start ASGI (Uvicorn) with main:app | Workers are also loaded and begin working through workload.
- App read environment variables and prepares FastAPI environment
- Load `app/main.py`.
- Core modules are loaded.
- Custom modules are loaded.
- Dependency checks for modules are done.
- Routes are included - Routes rely on module config?
- Lifespan method executed.
- Loaded databases are initialized
- Configuration is loaded.
- Cron checks are made and handlers called.
- Any custom methods outside of Cron and Routes, should be called from an endpoint.
- 
"""

# Load app/main.py
try:
    from app import main
except Exception as e:
    raise Exception(f"Failed to load app/main.py: {e}")

# Core and Custom modules are loaded and depdencies checked

# Include routes
log.info("Loading API Routes")
Module.load_routes(app)

# DEBUG - Loading NiceGUI Admin Panel
# NOTE - NiceGUI MUST be loaded before lifespan. Websockets dont work correctly if loaded after lifespan.
# ... Therefore, will have to use a different method to connect to the DB to retrieve configurations.

# If using AdminPanel - DEPRECATE - using else statement below.
# if 'admin_panel' in Module.loaded_modules:
#     pass
#     from core.admin import router as admin_router
#     app.include_router(admin_router, prefix="/admin", tags=["admin"])

# If using Frontend
if 'frontend' in Module.loaded_modules:
#     from core.frontend import router as frontend_router
#     app.include_router(frontend_router, prefix="/", tags=["frontend"])
    # @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    # async def frontend():
    #     pass
    pass

else:
    # Main page - If NOT using AdminPanel or Frontend
    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    async def home():
        _text = "<html><body><div style='margin-left:auto;margin-right:auto;max-width:400px;text-align:center; margin-top:20vh;'>"
        _text += "<h1 style='font-family: monospace;'> ヽ(•‿•)ノ </h1>"
        _text += f"<h1>{settings.PROJECT_NAME}</h1>"
        _text += "<p>"+settings.PROJECT_DESCRIPTION+"</p>"
        
        if 'admin_panel' in Module.loaded_modules:
            _text += f"<p><a href='{settings.ADMIN_PANEL_STR}'>Admin</a> | "
        
        _text += f"<a href='/docs'>Swagger Docs</a> | <a href='/redoc'>ReDoc Docs</a>"
        
        if settings.SENTRY_DSN:
            _text += " | <a href='https://sentry.io/organizations/' target='_blank'>Sentry</a>"

        if settings.DEBUG:
            pass
            
        _text += f"</p><p>Version: {settings.APP_VERSION}</body></html>" 
        return _text

@app.get("/health", include_in_schema=True)
async def health(background_tasks: BackgroundTasks):
    # TODO Start Cron Jobs
    return {"status": "ok"}

log.info("FastAPI Loaded")