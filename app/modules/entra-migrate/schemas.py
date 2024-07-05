# from mongoengine import Document, StringField, ListField, DateTimeField, ObjectIdField
from beanie import Document
from typing import List, Dict, Any, Union, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel

from sqlalchemy import Column, Integer, String, DateTime, JSON, ClauseList
from core.utils.sqlite import Base

"""
{
  "authority": "https://login.microsoftonline.com/...",
  "client_id": "...",
  "scope": [ "https://graph.microsoft.com/.default" ],
  "secret": "...",
  "endpoint": "https://graph.microsoft.com/v1.0/users",
  "baseurl": "https://graph.microsoft.com/v1.0"
}
"""

class Status(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    
class Tenant(Base):
    __tablename__ = 'entra_migrate_tenants'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    authority = Column(String)
    client_id = Column(String)
    scope = Column(String, default="https://graph.microsoft.com/.default", doc="Comma seperated List of scopes")
    secret = Column(String)
    baseurl = Column(String, default="https://graph.microsoft.com/v1.0")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class TenantCreate(BaseModel):
    name: str
    authority: str
    client_id: str
    scope: str = "https://graph.microsoft.com/.default"
    secret: str
    baseurl: str = "https://graph.microsoft.com/v1.0"
    # created_at: Optional[datetime] = datetime.now(timezone.utc)
    
# ## Remote, using MongoDB and Beanie
# class Tenant(Document):
#     name: str
#     authority: str
#     client_id: str
#     # scope: list = StringField(required=True)#ListField(StringField(), required=True)
#     scope: List[str] = ["https://graph.microsoft.com/.default"]
#     secret: str
#     baseurl: str = "https://graph.microsoft.com/v1.0"
#     created_at: Optional[datetime] = datetime.now(timezone.utc)
    
#     class Setting:
#         name = "entra_migrate_tenants"
    
#     @staticmethod
#     def schema_dump():
#         return {
#             "name": "",
#             "authority": "",
#             "client_id": "",
#             "scope": ["https://graph.microsoft.com/.default"],
#             "secret": "",
#             "baseurl": "https://graph.microsoft.com/v1.0",
#             # "created_at": datetime.now(timezone.utc),
#         }
        


    
# class MigrationJobs(Document):

#     created_at: datetime = datetime.now(timezone.utc)
#     source_tenant: str 
#     destination_tenants: List[str]
#     status: Status = Status.PENDING
#     apps: List[Dict]
    
#     class Setting:
#         name = "entra_migrate_jobs"

