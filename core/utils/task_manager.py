### Redis Queue Manager
from typing import Any, Dict, List, Union
from beanie import init_beanie
from beanie.odm.documents import Document
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from os import getenv
from loguru import logger as log
from enum import Enum
import traceback
from rq.types import FunctionReferenceType

from core.config import settings
# from tables.task import Task
# from vars import USING_DOCKER, DATABASE_NAME

# https://python-rq.org/
# Redis Queue
from rq import *
from redis import Redis

# if settings.USING_DOCKER: # Use the Redis container
#     redis_conn = Redis(host="rq_redis")
# else:
redis_conn = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, password=settings.REDIS_PASSWORD)

# _is_async = False if settings.RQ_BYPASS_WORKER else True
_is_async = not settings.RQ_BYPASS_WORKER
if _is_async:
    queue = Queue('task_manager', connection=redis_conn)
else:
    queue = Queue('task_manager', connection=redis_conn, is_async=False)
    

    
    
class TaskManager:
    
    queue = queue
    running_from_worker = True # Set to False in FastAPI, modules/admin/routes/rq.py when loaded.
    
    @staticmethod
    def _async_manager(func, *args, **kwargs):
        """
        Helper function to run the function asynchronously
        """
        log.debug("Running async task manager helper function")
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(func(*args, **kwargs))
        except RuntimeError:
            task = asyncio.create_task(func(*args, **kwargs))  # Python 3.7+
        except Exception as e:
            log.error(e)
            raise Exception(e)
        
        return
        # loop = asyncio.new_event_loop() 
        loop = asyncio.get_event_loop()
        # loop = asyncio.get_running_loop()
        # asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(func(*args, **kwargs))
        except Exception as e:
            log.error(e)
        # finally:
        #     loop.close()

        # loop = asyncio.get_event_loop()
        # return loop.run_until_complete(func(*args, **kwargs))
    
    # TODO Add more documentaiton and references
    @staticmethod
    def enqueue(func, *args, **kwargs
    ):
        """
        Enqueue a function to be processed by the RQ worker.
        
        Args:
            func: The function to be enqueued.
            args: Arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
            timeout: Optional[int] = None
            result_ttl: Optional[int] = None
            ttl: Optional[int] = None
            failure_ttl: Optional[int] = None
            description: Optional[str] = None
            depends_on: Optional['JobDependencyType'] = None
            job_id: Optional[str] = None
            at_front: bool = False
            meta: Optional[Dict] = None
            retry: Optional['Retry'] = None
            on_success: Optional[Union[Callback, Callable[..., Any]]] = None
            on_failure: Optional[Union[Callback, Callable[..., Any]]] = None
            on_stopped: Optional[Union[Callback, Callable[..., Any]]] = None
            pipeline: Optional['Pipeline'] = None
            is_async: bool = False # If task method is async, set this to True, it will run the function asynchronously
            
        Returns:
            Job: Job instance representing the enqueued job.
        """
        if 'failure_ttl' not in kwargs:
            kwargs['failure_ttl'] = 60*60*24*14 # 14 days
        if 'ttl' not in kwargs:
            kwargs['ttl'] = 60*60*24*7 # 7 days
            
        is_async = kwargs.pop('is_async', False)
        
        try:
            if TaskManager.queue:
                
                if is_async:
                    job = TaskManager.queue.enqueue(TaskManager._async_manager, func, *args, **kwargs)
                    print("Async Job:", job)
                    return job
                
                job = TaskManager.queue.enqueue(func, *args, **kwargs)
                return job
            
        except Exception as e:
            # TODO. if issues with connecting to Redis, fallback to synchronous processing + restart connection?
            log.error(e)
            traceback.print_exc()

        # fallback
        if is_async:
            pass
            job = TaskManager._async_manager(func, *args, **kwargs)
        else:
            job = func(*args, **kwargs)
    
    @staticmethod
    def enqueue_at(
        datetime: datetime,
        f: Any,
        *args: Any,
        **kwargs: Any
    ):
        """
        Schedules a job to be enqueued at specified time

        Args:
            datetime (datetime): _description_
            f (_type_): _description_

        Returns:
            _type_: _description_
        """
        try:
            if TaskManager.queue:
                job = TaskManager.queue.enqueue_at(datetime, f, *args, **kwargs)
                log.debug(job)
                if job:
                    return job
        except Exception as e:
            log.error(e)
            traceback.print_exc()
            
        # Fallback to synchronous processing?
        log.warning("Task was not scheduled due to an error with the Queue manager/Redis connection.")
        
        return None

    @staticmethod
    def enqueue_in(
        time_delta: timedelta,
        func: 'FunctionReferenceType',
        *args: Any,
        **kwargs: Any
    ):
        """
        Schedules a job to be executed in a given timedelta object

        Args:
            time_delta (timedelta): The timedelta object
            func (FunctionReferenceType): The function reference

        Returns:
            job (Job): The enqueued Job
        """
        return TaskManager.enqueue_at(datetime.now(timezone.utc) + time_delta, func, *args, **kwargs)

    @staticmethod
    async def init_beanie(tables: List[str] = []):
        """
        Shortcut helper function for Workers to initialize MongoDB Documents (Beanie) for the specified tables.
        Pass a list of table Document objects, or the full path to the table Document object as python import string.
        """
        try:
            client = AsyncIOMotorClient(settings.MONGODB_URI)
            # Specify the database
            database = client[settings.DATABASE_NAME]
            # database = client.get_default_database()
            log.info(f"Connecting to database: {database.name}")
            # We HAVE to import using full path to avoid issues with Beanie
            tables_list = tables
            
            # Initialize Beanie
            await init_beanie(database=database, document_models=tables_list)
            
        except Exception as e:
            log.error(e)
            