"""
DashUI Theme

This is a NiceGUI theme that is based on the DashUI theme. It is a simple and clean theme that is easy to use and customize. 
It is designed to be used with the NiceGUI framework, which is a simple and easy-to-use framework for building web applications.

The theme file preloads the colors, styles, fonts, and other design elements that are used in the theme. It also includes the layout and components that are used in the theme.

Inspiration: https://themewagon.com/themes/dashui/

"""

from contextlib import contextmanager


from nicegui import ui
from ..common.models import FrontendThemeBaseModel, Colors
from core.common import settings
from core.common import utc_now

class Theme(FrontendThemeBaseModel): # TODO Create a parent class that defines the common elements of a theme. frame, sidebar, etc.
    """
    Settings for the frontend Panel module.
    """
    colors: Colors = Colors(
        primary='#212B36',
        secondary='#2C384A',
        accent='#53B689',
        positive='#53B689',
        negative='#C10015',
        info='#31CCEC',
        warning='#F2C037',
        dark='#2c2c2c'
        
    )
    header_height: int = 60
    # default_left_sidebar_menu: callable = None
    
    @contextmanager
    def frame(self, navigation_title: str = "", sidebar_menu: callable = None):
        """Custom page frame to share the same styling and behavior across all pages"""
        # ui.colors(primary='#6E93D6', secondary='#53B689', accent='#111B1E', positive='#53B689')
        ui.colors(
            primary=self.colors.primary, 
            secondary=self.colors.secondary, 
            accent=self.colors.accent, 
            dark=self.colors.dark,
            positive=self.colors.positive, 
            negative=self.colors.negative, 
            info=self.colors.info, 
            warning=self.colors.warning
        )
        ui.add_css("""
            body, .bg-main {
                background-color: #F5F7FA;
            }
        """)
        with ui.left_drawer(top_corner=True, bottom_corner=True).classes('bg-primary text-white') as left_drawer:
            # TODO if have logo, use logo
            ui.label(settings.PROJECT_NAME).classes('font-bold text-lg text-light')
            if not sidebar_menu: sidebar_menu = self.default_left_sidebar_menu
            if sidebar_menu:
                with ui.column().classes('full-width'):
                    sidebar_menu(self)
                
        with ui.right_drawer(top_corner=True, value=False).props('bordered').classes('bg-white text-primary') as right_drawer:
            ui.label("Notifications").classes('font-bold text-lg text-primary')
            ui.separator()
            with ui.card().classes('full-width'):
                ui.label('Notification 1')
        
        with ui.header(elevated=True,bordered=True).props('full-width').classes('vertical-middle bg-white text-primary').style(f'height: {self.header_height}px;'):
            ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat round color=dark bg-dark')
            ui.space()
            with ui.button(on_click=lambda: right_drawer.toggle(), icon='notifications').props('outline flat round color=dark bg-dark clickable'):
                badge = ui.badge('3').props('color=accent floating')
            with ui.button().props('outline flat round color=dark clickable'):
                ui.icon('person')
            # with ui.avatar(icon='person', color='accent', size='md').props('fab color=accent cursor-pointer'):
                with ui.menu() as menu:
                    ui.menu_item('Menu item 1')
                    ui.menu_item('Menu item 2')
                    ui.menu_item('Menu item 3 (keep open)')
                    ui.separator()
                    ui.menu_item('Close', menu.close)

            
        with ui.footer(fixed=False).classes('text-primary bg-main'):
            ui.separator()
            today = utc_now()
            ui.label(f'© {today.year} {settings.PROJECT_NAME}')
            ui.space()
            ui.label(f'version {settings.APP_VERSION}')
            
        with ui.column().classes('full-width'):
            if navigation_title:
                ui.label(navigation_title).classes('text-2xl font-bold')
                ui.separator()
            yield
    
    @contextmanager
    def content(self, title:str = None, description:str = None, sidebar_callback:callable = None):
        with ui.row().classes('full-width'):
            with ui.column().classes('col-2'):
                if title:
                    ui.label(title).classes('text-xl')
                if description:
                    ui.label(description).classes('text-caption')
                if sidebar_callback:
                    ui.separator()
                    sidebar_callback()
            with ui.card().classes('col-8'):
                yield