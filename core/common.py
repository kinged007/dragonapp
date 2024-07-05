"""
A simple file that preloads some of the most common methods for quick and easy access.
"""
from core.utils.logging import logger as log, print
from core.config import settings
from core.utils.cache import global_cache
from core.utils.datetime import utc_now, utc_datetime, nice_time
from core.utils.task_manager import TaskManager

__all__ = [
    "log",
    "print",
    "settings",
    "global_cache",
    "utc_now",
    "utc_datetime",
    "nice_time",
    "TaskManager",
    
]