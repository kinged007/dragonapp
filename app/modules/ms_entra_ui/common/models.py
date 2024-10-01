from pydantic import BaseModel
from core.schemas.singleton import SingletonMeta
from contextlib import contextmanager
# from .theme import get_theme
from nicegui import APIRouter as nicegui_APIRouter, app as nicegui_app
from core.schemas.singleton import SingletonMeta
import functools
import asyncio
from core import Module
from ..common.menu import sidebar_menu
from core.events import trigger_event

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


class FrontendThemeBaseModel(metaclass=SingletonMeta):
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


class Frontend(metaclass=SingletonMeta):
    """
    Helper class for modules to create UI pages and Frontend components.
    """
    _router = nicegui_APIRouter()
    
    # @Frontend.router.page('/{id}', title='Migration Job', viewport='full', ...) # kwargs for @router.page
    @classmethod
    def router(cls, **kwargs) -> nicegui_APIRouter:
        """
        prefix: An optional path prefix for the router.
        tags: 
                A list of tags to be applied to all the *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).

        dependencies: 
                A list of dependencies (using `Depends()`) to be applied to all the
                *path operations* in this router.

                Read more about it in the
                [FastAPI docs for Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).

        default_response_class: 
                The default response class to be used.

                Read more in the
                [FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/#default-response-class).

        responses: 
                Additional responses to be shown in OpenAPI.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Additional Responses in OpenAPI](https://fastapi.tiangolo.com/advanced/additional-responses/).

                And in the
                [FastAPI docs for Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).

        callbacks: 
                OpenAPI callbacks that should apply to all *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for OpenAPI Callbacks](https://fastapi.tiangolo.com/advanced/openapi-callbacks/).

        redirect_slashes: 
                Whether to detect and redirect slashes in URLs when the client doesn't
                use the same format.

        default: 
                Default function handler for this router. Used to handle
                404 Not Found errors.

        dependency_overrides_provider: 
                Only used internally by FastAPI to handle dependency overrides.

                You shouldn't need to use it. It normally points to the `FastAPI` app
                object.

        route_class: 
                Custom route (*path operation*) class to be used by this router.

                Read more about it in the
                [FastAPI docs for Custom Request and APIRoute class](https://fastapi.tiangolo.com/how-to/custom-request-and-route/#custom-apiroute-class-in-a-router).

        on_startup: 
                A list of startup event handler functions.

                You should instead use the `lifespan` handlers.

                Read more in the [FastAPI docs for `lifespan`](https://fastapi.tiangolo.com/advanced/events/).

        on_shutdown: 
                A list of shutdown event handler functions.

                You should instead use the `lifespan` handlers.

                Read more in the
                [FastAPI docs for `lifespan`](https://fastapi.tiangolo.com/advanced/events/).
        lifespan: 
                A `Lifespan` context manager handler. This replaces `startup` and
                `shutdown` functions with a single context manager.

                Read more in the
                [FastAPI docs for `lifespan`](https://fastapi.tiangolo.com/advanced/events/).

        deprecated: 
                Mark all *path operations* in this router as deprecated.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
        include_in_schema:
                To include (or not) all the *path operations* in this router in the
                generated OpenAPI.

                This affects the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Query Parameters and String Validations](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/#exclude-from-openapi).
        generate_unique_id_function:
                Customize the function used to generate unique IDs for the *path
                operations* shown in the generated OpenAPI.

                This is particularly useful when automatically generating clients or
                SDKs for your API.

                Read more about it in the
                [FastAPI docs about how to Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/#custom-generate-unique-id-function).
        """
        if not cls._router:
                cls._router = nicegui_APIRouter(**kwargs)
        # return nicegui_APIRouter(**kwargs)
        return cls._router

    @classmethod
    def theme(cls) -> FrontendThemeBaseModel:
        # return get_theme()    
        module = Module.by_name(__name__)
        Theme = module.config.get_theme()
        Theme.default_left_sidebar_menu = sidebar_menu
        trigger_event('frontend_theme_get', theme=Theme)
        return Theme
    

    @classmethod
    def page(cls, path: str, title: str = None, **kwargs):
        """
        Decorator to create a new frontend Panel page.
        """
        def decorator(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                        with cls.theme().frame(title):
                                if asyncio.iscoroutinefunction(func):
                                        result = await func(*args, **kwargs)
                                else:
                                        result = func(*args, **kwargs)
                        return result

                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                        with cls.theme().frame(title):
                                return func(*args, **kwargs)

                if asyncio.iscoroutinefunction(func):
                        wrapper = async_wrapper
                else:
                        wrapper = sync_wrapper

                cls._router.page(path, title=title, **kwargs)(wrapper)
                return wrapper

        return decorator    


    @classmethod
    def include_router(cls, router, **kwargs):
        """
        Include the router in the Frontend app.
        
        router: The `APIRouter` to include.
        prefix: An optional path prefix for the router.
        tags: 
                A list of tags to be applied to all the *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).

        dependencies:
                A list of dependencies (using `Depends()`) to be applied to all the
                *path operations* in this router.

                Read more about it in the
                [FastAPI docs for Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).

                **Example**

                ```python
                from fastapi import Depends, FastAPI

                from .dependencies import get_token_header
                from .internal import admin

                app = FastAPI()

                app.include_router(
                    admin.router,
                    dependencies=[Depends(get_token_header)],
                )
                ```

        responses: 
                Additional responses to be shown in OpenAPI.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Additional Responses in OpenAPI](https://fastapi.tiangolo.com/advanced/additional-responses/).

                And in the
                [FastAPI docs for Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).

        deprecated: 
                Mark all the *path operations* in this router as deprecated.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                **Example**

                ```python
                from fastapi import FastAPI

                from .internal import old_api

                app = FastAPI()

                app.include_router(
                    old_api.router,
                    deprecated=True,
                )
                ```

        include_in_schema: 
                Include (or not) all the *path operations* in this router in the
                generated OpenAPI schema.

                This affects the generated OpenAPI (e.g. visible at `/docs`).

                **Example**

                ```python
                from fastapi import FastAPI

                from .internal import old_api

                app = FastAPI()

                app.include_router(
                    old_api.router,
                    include_in_schema=False,
                )
                ```

        default_response_class: 
                Default response class to be used for the *path operations* in this
                router.

                Read more in the
                [FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/#default-response-class).

                **Example**

                ```python
                from fastapi import FastAPI
                from fastapi.responses import ORJSONResponse

                from .internal import old_api

                app = FastAPI()

                app.include_router(
                    old_api.router,
                    default_response_class=ORJSONResponse,
                )
                ```

        callbacks: 
                List of *path operations* that will be used as OpenAPI callbacks.

                This is only for OpenAPI documentation, the callbacks won't be used
                directly.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for OpenAPI Callbacks](https://fastapi.tiangolo.com/advanced/openapi-callbacks/).

        generate_unique_id_function: 
                Customize the function used to generate unique IDs for the *path
                operations* shown in the generated OpenAPI.

                This is particularly useful when automatically generating clients or
                SDKs for your API.

                Read more about it in the
                [FastAPI docs about how to Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/#custom-generate-unique-id-function).
        """
        nicegui_app.include_router(cls._router, **kwargs, include_in_schema=True)