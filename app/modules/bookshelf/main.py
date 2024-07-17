"""
This is an example module for a bookshelf application.
"""
from fastapi import APIRouter
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from core import Module
from core.utils.logging import logger as log
from core.schemas import database, module_config
from core.utils.endpoints import CRUDJsonEndpoints

# Define the configuration class
class BookShelfConfig(module_config.BaseModuleConfig):
    """
    Configuration for the Bookshelf module
    """
    # Add configuration options here
    pass

# Define the database tables
class Author(database.DatabaseMongoBaseModel):
    name: str
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    biography: Optional[str] = None

    class Settings:
        name = "bookshelf_authors"
    
    class Config:
        # Required for database references
        # TODO implement at parent class level, so its automatic
        json_schema_extra = {
            "collection_name": "bookshelf_authors",
            "type": "database_ref",
            "display_field": "Big Dog {name}"
        }

class Publisher(database.DatabaseMongoBaseModel):
    name: str
    founded: Optional[date] = None
    country: Optional[str] = None

    class Settings:
        name = "bookshelf_publishers"
    
    class Config:
        # Required for database references
        json_schema_extra = {
            "collection_name": "bookshelf_publishers",
            "type": "database_ref"
        }

class Tag(database.DatabaseMongoBaseModel):
    name: str
    description: Optional[str] = None

    class Settings:
        name = "bookshelf_tags"
    
    class Config:
        # Required for database references
        json_schema_extra = {
            "collection_name": "bookshelf_tags",
            "type": "database_ref"
        }

class Book(database.DatabaseMongoBaseModel):
    title: str
    authors: List[Author]
    # publisher: Publisher
    publication_date: Optional[date] = None
    isbn: Optional[str] = None
    pages: Optional[int] = None
    language: Optional[str] = None
    tags: List[Tag] = []
    summary: Optional[str] = None

    class Settings:
        name = "bookshelf_books"
    
    class Config:
        # Required for database references
        json_schema_extra = {
            "collection_name": "bookshelf_books",
            "type": "database_ref"
        }

# class User(database.DatabaseMongoBaseModel):
#     id: int
#     username: str
#     email: str
#     full_name: Optional[str] = None
#
# class Settings:
#     name = "bookshelf_users"

# class Review(database.DatabaseMongoBaseModel):
#     id: int
#     book: Book
#     user: User
#     rating: int = Field(..., ge=1, le=5)  # rating should be between 1 and 5
#     review_text: Optional[str] = None
#     review_date: date

# class Settings:
#     name = "bookshelf_reviews"
    
# Define the API router
api_router = APIRouter()

# Define the CRUD endpoints
CRUDJsonEndpoints(
    api_router,
    base_name="Bookshelf",
    collection=[Author, Publisher, Book, Tag],
    # database=[Author, Publisher, Tag, Book],
    method=['GET', 'POST', 'PATCH', 'DELETE'],
    # tags=['Bookshelf'], # Auto tag
    # name_singluar='Book', # Auto apply
    # name_plural='Books', # temp
    description='The easiest to use Bookshelf API.',
).build()

# Define the module
Module.register(
    __name__,
    title='Bookshelf',
    config_class=BookShelfConfig,
    database=[Author, Publisher, Tag, Book],
    description="A simple bookshelf application",
    version="0.1.0",
    router=api_router,
    events=[
        # ('event_name', callback_function)
        ('admin_theme_get', lambda theme: log.info(f"Admin theme is {theme.__class__}") ),
    ],
)