"""
Logging module. Extends the loguru logger.

"""

import sys
from loguru import logger
from builtins import print as builtin_print
from core.config import settings

def log_level(level:str = None):
    """
    Returns log level as numeric value. If no parameter is passed, returns the log level of the LOGGING_LEVEL environment variable.
    """
    _levels = {
        "DEBUG" : 0,
        "INFO" : 1,
        "WARNING" : 2,
        "ERROR" : 3,
    }
    
    if level:
        return _levels.get(level.upper(), 1)
    return _levels.get(settings.LOGGING_LEVEL, 1)


def setup_logger():
    logger.remove()
    logger.add("logs/default.log", level=settings.LOGGING_LEVEL, rotation="5 MB", compression="zip", retention="30 days")
    logger.add("logs/errors.log", level="WARNING", rotation="5 MB", compression="zip", retention="30 days", backtrace=True, diagnose=True)
    logger.add("logs/errors.log", level="ERROR", rotation="5 MB", compression="zip", retention="30 days", backtrace=True, diagnose=True)
    if settings.DEBUG:
        logger.add("logs/debug.log", level="DEBUG", rotation="5 MB", compression="zip", retention="7 days")
        logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, level=settings.LOGGING_LEVEL)

# Run the setup function
setup_logger()

logger.info(f"Debug Mode = {settings.DEBUG}, Logging level = {settings.LOGGING_LEVEL}")

def print(*args, **kwargs):
    if not settings.DEBUG:
        builtin_print("Debug mode is disabled. Set DEBUG=True in the environment to enable printing output to console.")
        return
    try:
        from rich import print
    except ImportError:
        # builtin_print("Rich not installed. Install it with 'pip install rich'.")
        print = builtin_print
        pass
    print(*args, **kwargs)
    
# Initialize MongoDB client
# client = AsyncIOMotorClient('mongodb://localhost:27017')
# db = client['log_database']
# collection = db['log_collection']

# class DatabaseHandler():
#     def emit(self, record):
#         log_entry = self.format(record)
#         self.write(log_entry)

#     def write(self, msg):
#         # await collection.insert_one({"message": msg})
#         print("LOGGING:", msg)
#         # print(type(msg['record']), str(msg['record'].__dict__))
#         pass

# # Remove default handler
# logger.remove()
# # Add custom handler
# logger.add(DatabaseHandler(), level=getenv("LOGGING_LEVEL", "INFO").upper())