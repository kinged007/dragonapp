import pymongo
from enum import Enum
from pydantic import BaseModel, HttpUrl, Field, validator, AnyUrl
from typing import Optional, List, Dict, Annotated, Any
from datetime import datetime
from beanie import Document, Indexed

from core.schemas.database import DatabaseMongoBaseModel
from pymongo import IndexModel
from core.utils.datetime import utc_now

# API Schemas
# TODO Implement SQLite database for readonly data - ie. analytics

class DeviceRedirects(BaseModel):
    android: Optional[HttpUrl] = None
    ios: Optional[HttpUrl] = None
    desktop: Optional[HttpUrl] = None
    
class ShortLinkMeta(BaseModel):
    valid_since: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_visits: Optional[int] = None
    
class ShortLinkVisitsSummary(BaseModel):
    total: int = 0
    non_bots: int = 0
    bots: int = 0
    
class ShortLinkVisitLocation(BaseModel):
    countryCode: Optional[str] = None
    countryName: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    regionName: Optional[str] = None
    timezone: Optional[str] = None
    cityName: Optional[str] = None
    isEmpty: bool = True

class ShortLinkRequest(BaseModel):
    url: Annotated[HttpUrl, Field(..., description="The URL to shorten")]
    alias: Optional[str] = None
    tags: Optional[List[str]] = []
    domain: Optional[str] = Field(..., pattern=r'^[a-zA-Z0-9]+([\-\_\.]{1}[a-zA-Z0-9]+)*\.[a-zA-Z]{2,5}$', examples=["example.com"])
    forward_query_params: Optional[bool] = False
    device_redirects: Optional[DeviceRedirects] = None
    expires_at: Optional[datetime] = None

class ShortLinkRedirect(BaseModel):
    url: str
    response_code: int = 301

class ShlinkDomainPostPatch(BaseModel):
    id: Optional[str] = None
    domain: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9]+([\-\_\.]{1}[a-zA-Z0-9]+)*\.[a-zA-Z]{2,5}$', examples=["example.com"])
    is_active: Optional[bool] = None
    
## Database Schemas

class ShlinkDomainDocument(DatabaseMongoBaseModel):
    domain: str = Field(..., pattern=r'^[a-zA-Z0-9]+([\-\_\.]{1}[a-zA-Z0-9]+)*\.[a-zA-Z]{2,5}$', examples=["example.com"])
    is_active: bool = True
    created_at: datetime = utc_now()
    updated_at: Optional[datetime] = None
    
    @validator('domain', pre=True)
    def lowercase_domain(cls, v):
        return v.lower()
    
    class Settings:
        name = "shlink_domains"
        indexes = [
            IndexModel("domain", unique=True),
        ]
        endpoints_updated_field = "updated_at"
        endpoints_readonly_fields = ["created_at", "updated_at"]


class ShlinkAnalyticsDocument(DatabaseMongoBaseModel):
    short_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]*$', examples=["abc123"])
    date: datetime = utc_now()
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    referrer: Optional[str] = ""
    potential_bot: bool = False
    visit_location: Optional[ShortLinkVisitLocation] = None
    language: Optional[str] = None
    
    server_data: Optional[Dict[str, Any]] = {}
    
    class Settings:
        name = "shlink_analytics"
        # endpoints_readonly_fields = ["accessed_at"] # remove read-only fields for migrations


class ShlinkShortLinkDocument(DatabaseMongoBaseModel):
    short_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]*$', examples=["abc123"])
    # url: str = Field(..., pattern=r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$')
    short_url: Optional[HttpUrl] = Field(None, description="The short URL to be used.", examples=["https://example.com/abc123"])
    url: HttpUrl = Field(..., description="The URL to redirect to", examples=["https://long_url_to_shorten.com"])
    alias: Optional[str] = None
    domain: str
    created_at: datetime = utc_now()
    updated_at: Optional[datetime] = None
    tags: List[str] = []
    device_redirects: DeviceRedirects = DeviceRedirects()
    meta: ShortLinkMeta = ShortLinkMeta()
    title: Optional[str] = None
    visits_count: int = 0
    visits_summary: ShortLinkVisitsSummary = ShortLinkVisitsSummary()
    forward_query_params: bool = False
    # expires_at: Optional[datetime] = None
    # referrers: Dict[str, int] = {}
    
    @validator('domain', pre=True)
    def lowercase_domain(cls, v):
        return v.lower()

    class Settings:
        name = "shlink_short_links"
        indexes = [
            IndexModel("short_id", unique=True),
        ]
        endpoints_updated_field = "updated_at"
        endpoints_readonly_fields = [ "updated_at","short_url"] #"created_at",