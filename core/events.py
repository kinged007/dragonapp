"""
This module handles all the events and hooks for the app.

The main objective of this module is to provide a way to hook into the app and provide custom functionality.
With this, the app will trigger events which can be later used to execute custom code.
"""
from core.module_manager import Module
from core.common import log


def trigger_event(event_name:str, module:str = None, *args, **kwargs):
    """
    Trigger an event with the given name. The format follows the following logic:
    If the module is provided, then the event is triggered for that module only.
    
    Args:
        event_name (str): The name of the event to trigger. 
    """
    # Trigger the event for the module only.
    log.debug(f"Triggering EVENT: {event_name}")
    callbacks = Module.find_event_callbacks(event_name, module)
    for callback in callbacks:
        callback(*args, **kwargs)
    # TODO allow events to be run asyncronously or in background.
        