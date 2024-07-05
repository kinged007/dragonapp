from pydantic import BaseModel
from core.schemas.singleton import SingletonMeta
from contextlib import contextmanager


class Colors(BaseModel):
    primary: str = None
    secondary: str = None
    accent: str = None
    dark: str = None
    positive: str = None
    negative: str = None
    info: str = None
    warning: str = None
    def __init__(self, *,
                 primary='#5898d4',
                 secondary='#26a69a',
                 accent='#9c27b0',
                 dark='#1d1d1d',
                 positive='#21ba45',
                 negative='#c10015',
                 info='#31ccec',
                 warning='#f2c037') -> None:
        """Color Theming

        Sets the main colors (primary, secondary, accent, ...) used by `Quasar <https://quasar.dev/>`_.
        """
        super().__init__()
        self.primary = primary
        self.secondary = secondary
        self.accent = accent
        self.dark = dark
        self.positive = positive
        self.negative = negative
        self.info = info
        self.warning = warning


class AdminThemeBaseModel(metaclass=SingletonMeta):
    """
    This is the basemodel for all NiceGUI Themes
    """
    model_config: dict = {
        "arbitrary_types_allowed": True,
    }
    
    colors: Colors = Colors()
    default_left_sidebar_menu: callable = None
    header_height: int = 60
    
    @contextmanager
    def frame(self, navigation_title: str = "", sidebar_menu: callable = None):
        """
        Applies the header, sidebars and footer to the page according to the Theme style.
        """
        yield
    
    @contextmanager
    def content(self, title:str = None, description:str = None, sidebar_callback:callable = None):
    # def content(self):
        """
        Optional contenet placeholder. The theme can use this to define a layout for the content area of the page.
        """
        yield
