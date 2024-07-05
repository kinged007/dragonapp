# Beanie tables to Load on Startup + Schema classes to be used throughout the module
# Classes with the Document class are automatically loaded into the database at startup

from beanie import Document, PydanticObjectId
from pydantic import ConfigDict, BaseModel, EmailStr
from enum import Enum
from fastapi_users.db import BeanieBaseUser
from fastapi_users_db_beanie import BeanieUserDatabase
from fastapi_users import schemas
    
class User(BeanieBaseUser, Document):
    pass


class UserRead(schemas.BaseUser[PydanticObjectId]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


async def get_user_db():
    yield BeanieUserDatabase(User)
