from typing import Callable, List, Type, Optional, Union, Tuple, Any
from pydantic import BaseModel, Field
from beanie import Document
from enum import Enum



class SortOrder(Enum):
    asc = "asc"
    desc = "desc"
    
class CRUDResponseModelGet(BaseModel):
    status_code: int = 200
    message: str = "success"
    data: List[dict] = []
    page: int = 1
    total_pages: int = 1
    per_page: int = 10
    total_items: int = 0
    
class CRUDResponseModelPostMany(BaseModel):
    status_code: int
    message: str
    success: Optional[List[Union[dict, str]]] = None
    errors: Optional[List[Union[dict, str]]] = None

class CRUDResponseModelDelete(BaseModel):
    status_code: int
    message: str

class CRUDQueryData(BaseModel):
    data: Optional[dict] = None # Used for the query to the database or item data being used
    # data: Optional[dict] = None
    request: Optional[dict] = None # Request data
    method: Optional[str] = None # Method being used
    