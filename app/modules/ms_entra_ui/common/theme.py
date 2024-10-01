# from ..config import frontend_config as apc
from core import Module
from ..common.menu import sidebar_menu
from ..common.models import FrontendThemeBaseModel
from core.events import trigger_event

def get_theme() -> FrontendThemeBaseModel:
    module = Module.by_name(__name__)
    Theme = module.config.get_theme()
    Theme.default_left_sidebar_menu = sidebar_menu
    trigger_event('frontend_theme_get', theme=Theme)
    return Theme
# Theme = apc.get_theme()