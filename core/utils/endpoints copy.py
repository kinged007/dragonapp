"""
The Endpoints Utility module provides a class to create CRUD endpoints for JSON data. 
It is designed to work with FastAPI and Beanie, and can be used to quickly create typical endpoints for a collection in a MongoDB database.


"""

from core import log
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request, Body
from fastapi.responses import JSONResponse  
from starlette.routing import BaseRoute
from typing import Callable, List, Type, Optional, Union, Tuple, Any
from pydantic import BaseModel, Field
from pymongo import errors as pymongo_errors
from bson import ObjectId
from beanie import Document
from math import ceil
from enum import Enum
import bsonjs
from bson.raw_bson import RawBSONDocument

from .datetime import utc_now
from .cache import SimpleCache


from core.schemas.endpoints import CRUDResponseModelGet, CRUDResponseModelPostMany, CRUDResponseModelDelete, CRUDQueryData, SortOrder


class CRUDJsonEndpoints:
    """
    Class to build CRUD endpoints for JSON data for "GET","POST", "PATCH", "DELETE" methods. Interacts directly with the database collection to process data.
    Requires:
        - router: FastAPI APIRouter instance
        - collection: Beanie Document class for the database collection. # TODO default to PyMongo database types, using DragonApp DatabaseMongoBaseModel schema.
        # TODO - Add support for SQLModel
        # TODO - add a Schema endpoint, to return the schema of the collection.
        - input_model and output_model: Pydantic models for input and output data. If not provided, the collection model will be used.
            - Use Class Settings to apply additional settings to the models (Beanie / Pydantic)
        - name_singluar and name_plural: Names for the collection. Singular will create one item endpoint, and plural will create get_all endpoint. At least one must be provided. 
        - method: HTTP method to create the endpoint for. Can be a string or a list of strings.
        - input_hook and output_hook: Functions to execute once input has been received and validated before the db query, and before output is sent, for validation processing and to modify the content. Accepts BaseRoute or Callable functions. 
        - completed_callbacks: List of functions to execute after the endpoint has been executed. Built in FastAPI callbacks, require BaseRoute (endpoint) function.
    
    Model Settings:
        Use the following parameters to apply additional settings to the models, other than that what can be normally applied by default (eg. type and required):
        - endpoints_readonly_fields : List of fields that are read only. These fields cannot be updated through the API endpoints. Only in the module logic.
        - endpoints_updated_field: Field to update with the current datetime when the document is updated.
        
    """
    def __init__(
        self,
        router: APIRouter,
        collection: Optional[Type[Document]] = None,
        prefix: Optional[str] = "",
        method: Union[str, List[str]] = ["GET","POST","PATCH","DELETE"], # TODO create an Enum model to select GET.Single, GET.Many, ...
        name_singluar: Optional[str] = None, # TODO Deprecate. Use plural name for all endpoints.
        name_plural: Optional[str] = None,
        dependencies: Optional[List[Depends]] = None,
        options: Optional[dict] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        output_model: Type[BaseModel] = None,
        input_model: Type[BaseModel] = None,
        return_item_data_on_error: bool = False,
        input_hook: Union[Callable, BaseRoute] = None,
        output_hook: Union[Callable, BaseRoute] = None,
        completed_callbacks: List[BaseRoute] | None = None, # Called after the endpoint has been executed. TODO if process is sent to background, how will this work?
        process_in_background: bool = False, # TODO change this to a background_callbacks, ie. a function to execute in the background with the data from the endpoint. 
        cache_ttl: Optional[int] = None, # TODO If none, cache will not be used. POST/PATCH/DELETE requests will automatically clear the cache.
    ):
        """
        Set default values for the CRUDJsonEndpoints class. If a value is defined here, and not overwritten in the build() method, the default value will be used.
        """
        self.router = router
        self.prefix = prefix.rstrip("/")
        self.dependencies = dependencies
        self.method = method
        self.collection = collection
        self.options = options
        self.tags = tags
        self.description = description        
        self.input_hook = input_hook
        self.output_hook = output_hook
        self.completed_callbacks = completed_callbacks
        self.include_in_schema = include_in_schema        
        self.name_singluar = name_singluar.strip("/").lower() if name_singluar else None
        self.name_plural = name_plural.strip("/").lower() if name_plural else None
        if output_model and "id" not in self.output_model.__annotations__:
            raise ValueError("Output model must have an ID field")
        self.output_model = output_model if output_model else self.collection
        self.input_model = input_model if input_model else self.collection
        self.return_item_data_on_error = return_item_data_on_error
        self.process_in_background = process_in_background
        self.cache_ttl = cache_ttl
        self._cache = SimpleCache()
        
        # self.create_endpoint()
    
    def _execute_callback(self, callback : Union[Callable, BaseRoute] = None , query: CRUDQueryData = None, output: Any = None):
        if callback:
            # Executes the call back depending on what type it is
            return callback(query, output)
        return output 
        
    def create_endpoint(self):
        log.opt(depth=2).warning("Creating endpoints from init() is no longer supported. It will be removed in future versions. Use .build() instead.", stacklevel=3)
    
    def clear_cache(self):
        """
        Clears the cache. Automatically called from internal POST, PATCH and DELETE. Can be called externally to clear the cache.
        """
        self._cache.clear()
    
    def get(self,
        name_singluar: Optional[str] = None,
        name_plural: Optional[str] = None,
        dependencies: Optional[List[Depends]] = None,
        options: Optional[dict] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        input_hook: Union[Callable, BaseRoute] = None,
        output_hook: Union[Callable, BaseRoute] = None,
        completed_callbacks: List[BaseRoute] | None = None,
        include_in_schema: bool = True,
        output_model: Type[BaseModel] = None,
        input_model: Type[BaseModel] = None,
        return_item_data_on_error: bool = False,
        process_in_background: bool = False, 
        ):
        return self.build(method="get", name_singluar=name_singluar, name_plural=name_plural, dependencies=dependencies, options=options, tags=tags, description=description, input_hook=input_hook, output_hook=output_hook, completed_callbacks=completed_callbacks, include_in_schema=include_in_schema, output_model=output_model, input_model=input_model, return_item_data_on_error=return_item_data_on_error, process_in_background=process_in_background)

    def post(self,
        name_singluar: Optional[str] = None,
        name_plural: Optional[str] = None,
        dependencies: Optional[List[Depends]] = None,
        options: Optional[dict] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        input_hook: Union[Callable, BaseRoute] = None,
        output_hook: Union[Callable, BaseRoute] = None,
        completed_callbacks: List[BaseRoute] | None = None,
        include_in_schema: bool = True,
        output_model: Type[BaseModel] = None,
        input_model: Type[BaseModel] = None,
        return_item_data_on_error: bool = False,
        process_in_background: bool = False, 
        ):
        return self.build(method="post", name_singluar=name_singluar, name_plural=name_plural, dependencies=dependencies, options=options, tags=tags, description=description, input_hook=input_hook, output_hook=output_hook, completed_callbacks=completed_callbacks, include_in_schema=include_in_schema, output_model=output_model, input_model=input_model, return_item_data_on_error=return_item_data_on_error, process_in_background=process_in_background)

    def patch(self,
        name_singluar: Optional[str] = None,
        name_plural: Optional[str] = None,
        dependencies: Optional[List[Depends]] = None,
        options: Optional[dict] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        input_hook: Union[Callable, BaseRoute] = None,
        output_hook: Union[Callable, BaseRoute] = None,
        completed_callbacks: List[BaseRoute] | None = None,
        include_in_schema: bool = True,
        output_model: Type[BaseModel] = None,
        input_model: Type[BaseModel] = None,
        return_item_data_on_error: bool = False,
        process_in_background: bool = False, 
        ):
        return self.build(method="patch", name_singluar=name_singluar, name_plural=name_plural, dependencies=dependencies, options=options, tags=tags, description=description, input_hook=input_hook, output_hook=output_hook, completed_callbacks=completed_callbacks, include_in_schema=include_in_schema, output_model=output_model, input_model=input_model, return_item_data_on_error=return_item_data_on_error, process_in_background=process_in_background)
        
    def delete(self,
        name_singluar: Optional[str] = None,
        name_plural: Optional[str] = None,
        dependencies: Optional[List[Depends]] = None,
        options: Optional[dict] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        input_hook: Union[Callable, BaseRoute] = None,
        output_hook: Union[Callable, BaseRoute] = None,
        completed_callbacks: List[BaseRoute] | None = None,
        include_in_schema: bool = True,
        output_model: Type[BaseModel] = None,
        input_model: Type[BaseModel] = None,
        return_item_data_on_error: bool = False,
        process_in_background: bool = False, 
        ):
        return self.build(method="delete", name_singluar=name_singluar, name_plural=name_plural, dependencies=dependencies, options=options, tags=tags, description=description, input_hook=input_hook, output_hook=output_hook, completed_callbacks=completed_callbacks, include_in_schema=include_in_schema, output_model=output_model, input_model=input_model, return_item_data_on_error=return_item_data_on_error, process_in_background=process_in_background)
        
    def build(self,
        method: Optional[Union[str, List[str]]] = None,
        name_singluar: Optional[str] = None,
        name_plural: Optional[str] = None,
        dependencies: Optional[List[Depends]] = None,
        options: Optional[dict] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        input_hook: Union[Callable, BaseRoute] = None,
        output_hook: Union[Callable, BaseRoute] = None,
        completed_callbacks: List[BaseRoute] | None = None, # Called after the endpoint has been executed. TODO if process is sent to background, how will this work?
        include_in_schema: bool = True,
        output_model: Type[BaseModel] = None,
        input_model: Type[BaseModel] = None,
        return_item_data_on_error: bool = False,
        process_in_background: bool = False, # TODO If true, will process the request in the background using a worker.
        collection: Optional[Type[Document]] = None,
        ):        
        
        ########################################################################
        ### Define the endpoint settings
        ########################################################################
        
        method = method if method else self.method
        name_singluar = name_singluar.strip("/").lower() if name_singluar else self.name_singluar
        name_plural = name_plural.strip("/").lower() if name_plural else self.name_plural
        if not name_singluar and not name_plural:
            raise ValueError("At least one of name_singluar or name_plural must be provided")
        dependencies = dependencies if dependencies else self.dependencies
        options = options if options else self.options
        tags = tags if tags else self.tags
        description = description if description else self.description
        input_hook = input_hook if input_hook else self.input_hook
        output_hook = output_hook if output_hook else self.output_hook
        completed_callbacks = completed_callbacks if completed_callbacks else self.completed_callbacks
        include_in_schema = include_in_schema if include_in_schema else self.include_in_schema
        return_item_data_on_error = return_item_data_on_error if return_item_data_on_error else self.return_item_data_on_error
        process_in_background = process_in_background if process_in_background else self.process_in_background
        if output_model and "id" not in output_model.__annotations__:
            raise ValueError("Output model must have an ID field")
        if collection: # Collection has changed. Double check input/output models
            output_model = output_model if output_model else collection
            input_model = input_model if input_model else collection
        output_model = output_model if output_model else self.output_model
        input_model = input_model if input_model else self.input_model
        collection = collection if collection else self.collection

        if not collection:
            raise ValueError("Collection must be provided")
        
        # endpoint creation with FastAPI router
        if isinstance(method, str):
            method = [method]
        
        # print(name_plural, collection, input_model, output_model, input_hook)
        # Name - use snake case etc to create name
        # name_singluar = f"{self.prefix}/{self.name_singluar}"
        # name_plural = f"{self.prefix}/{self.name_plural}" if self.name_plural else f"{self.prefix}/{self.name_singluar}s"
        
        ########################################################################
        ######## Endpoints
        ########################################################################
        
        #### SCHEMA ####
        # TODO - add an endpoint to retrieve the schema of a collection. Uses pydantics schema() method.
        
        #### GET ENDPOINTS ####
        
        # @self._cache.async_cache(ttl=self.cache_ttl)
        async def get_many_endpoint(
                request: Request,
                page: int = Query(1, description="Current page of the collection"),
                per_page: int = Query(100, description="Number of items per page"),
                sort_by: Optional[str] = Query(None, description="Field to sort by"),
                sort_order: Optional[SortOrder] = Query(SortOrder.asc, description="Sort order for the results", example="asc"),
                search: Optional[str] = Query(None, description="Limit results to those matching a string"),
                exclude: Optional[str] = Query(None, title="Exclude Fields", description="Fields to exclude from the results. Comma separated list of field names."),
                include: Optional[str] = Query(None, title="Include Fields", description="Fields to include in the results. Comma separated list of field names."),
                # TODO - Add filters
                filter: Optional[str] = Query(None, description="Filter results using JSON Extended Syntax. See https://www.mongodb.com/docs/manual/reference/mongodb-extended-json/#examples for more information."),
            ): 
            # log.error("Fetching many") # DEBUG
            # print(self.cache_ttl)
            # print(self._cache.storage)
            if per_page > 1000:
                per_page = 1000
            if per_page < 1:
                per_page = 100
            skip = (page - 1) * per_page
            
            query = {}
            if search:
                query["$text"] = {"$search": search}
            if filter:
                try:
                    bsion = bsonjs.loads(filter)
                    query.update(RawBSONDocument(bsion))
                except Exception as e:
                    log.error(e)
                    return JSONResponse(status_code=400, content={"message": "Invalid filter provided. Please check the syntax. Refer to https://www.mongodb.com/docs/manual/reference/mongodb-extended-json/#examples for more information.", "error": str(e)})
                
            sort_order_value = 1 if sort_order == SortOrder.asc else -1
            sort = [(sort_by, sort_order_value)] if sort_by else None
            
            try:
                active_count = await collection.find(query).count()
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=400, content={"message": "Error with query.", "error": str(e)})    

            try:
                items = await collection.find(query).sort(sort).skip(skip).limit(per_page).to_list()   
                _hook = self._execute_callback(input_hook, query=CRUDQueryData(data=query, method="get",request=request), output=items) # TODO Move first callback to BEFORE the database query is made
                if _hook: items = _hook
            except pymongo_errors.PyMongoError as e:
                return JSONResponse(status_code=400, content={"message": f"Error: {e}"})
            except Exception as e:
                if "index required" in str(e):
                    return JSONResponse(status_code=409, content={"message": "An Index on the Collection has not been found. Please create a text index on the collection or avoid using the search parameter."})
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})
            
            try:
                output = [output_model(**item.model_dump()).model_dump() for item in items]
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})
            
            if include:
                include = include.split(",")
                output = [{key: item[key] for key in include} for item in output]
            elif exclude:
                exclude = exclude.split(",")
                output = [{key: item[key] for key in item if key not in exclude} for item in output]         
            
            _hook = self._execute_callback(output_hook, query=CRUDQueryData(data=query, method="get",request=request), output=output)
            if _hook: output = _hook
            
            try:
                return {"data": output, "status_code": 200, "current_page": page, "total_pages": int(ceil(active_count/per_page)), "per_page": per_page, "total_items": active_count}
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})

        async def get_one_endpoint(
                request: Request,
                id: str = Path( description="ID of the item to retrieve", required=True ),
            ):
            
            try:
                items = await collection.find_one({"_id":ObjectId(id)}) 
                _hook = self._execute_callback(input_hook, query=CRUDQueryData(data={"_id":ObjectId(id)}, method="get",request=request), output=items)
                if _hook: items = _hook
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})
            
            try:
                if not items:
                    return JSONResponse(status_code=404, content={"message": "Item not found"})   
                _hook = self._execute_callback(output_hook, query=CRUDQueryData(data={"_id":ObjectId(id)}, method="get",request=request), output=items)
                if _hook: items = _hook
                return output_model(**items.model_dump()).model_dump(exclude_none=True) 
            except pymongo_errors.PyMongoError as e:
                return JSONResponse(status_code=400, content={"message": f"Error: {e}"})
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})
    
        #### POST ENDPOINTS ####
        async def post_endpoint(
                request: Request,
                data: Union[input_model, List[input_model]],
            ): 
            if not data:
                return JSONResponse(status_code=400, content={"message": "No data provided"})
            
            data = data if isinstance(data, list) else [data]
            
            if len(data) > 1000:
                return JSONResponse(status_code=400, content={"message": "Too many items to insert. Limit to 1000 items."})
            
            _to_insert = []
            completed = []
            errors = []
            for item in data:
                try: 
                    for _id in ['id','_id']:
                        if hasattr(item, _id):
                            delattr(item, _id)
                        # return JSONResponse(status_code=400, content={"message": "ID field cannot be provided. Use PATCH method instead to update items."})
                    try:
                        # Check if field is read only
                        for key in collection.Settings.endpoints_readonly_fields:
                            if hasattr(item, key):
                                log.warning(f"Field {key} is read only and should not be in the input_model. ")
                                # setattr(item, key, None)
                                delattr(item, key)
                    except:
                        pass
                    row = collection(**item.model_dump())
                    _hook = self._execute_callback(input_hook, query=CRUDQueryData(data=item.model_dump(), method="post",request=request), output=row)
                    if _hook: row = _hook
                    _to_insert.append(row)
                except pymongo_errors.PyMongoError as e:
                    _e = str(e).split("full error:")[0] if "full error:" in str(e) else e
                    errors.append({"message": f"Error: {_e}", "data": str(item.model_dump()) if return_item_data_on_error else None})
                except Exception as e:
                    log.error(e)
                    errors.append({"message": "Malformed data.", "data": str(item.model_dump())  if return_item_data_on_error else None}) 
            
            try:
                if _to_insert:
                    insert = await collection.insert_many(_to_insert) 
                    query = {"_id": {"$in": insert.inserted_ids}}
                    documents = await collection.find(query).to_list(None)
                    completed = [output_model(**item.model_dump()).model_dump() for item in documents]

                    # If an error occurs, it will raise an exception
                    
                if not completed:
                    return JSONResponse(status_code=400, content={"message": "Failed to insert data. Check the data and try again.", "errors": errors})
                
                completed_hook = self._execute_callback(output_hook, query=CRUDQueryData(data=None, method="post",request=request), output=completed)
                if completed_hook: completed = completed_hook
                
                return {
                    "status_code": 200, "message": f"Sucessfully saved {len(completed)} {name_plural.capitalize()}, with {len(errors)} errors.", "success": completed, "errors": errors}
            except pymongo_errors.BulkWriteError as e:
                return JSONResponse(status_code=400, content={"message": f"Error: {e}"})
            except pymongo_errors.PyMongoError as e:
                _e = str(e).split("full error:")[0] if "full error:" in str(e) else e
                return JSONResponse(status_code=400, content={"message": f"Error: {_e}"})
                # errors.append({"message": f"Error: {_e}", "data": item.model_dump() if return_item_data_on_error else None})
            except Exception as e:
                log.error(e)
                # errors.append({"message": "Something went wrong. Please see the logs.", "data": row.model_dump_json()  if return_item_data_on_error else None}) 
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})
            
        #### PUT / PATCH ENDPOINTS ####
        async def patch_many_endpoint( # DEBUG
                request: Request,
                data: Union[List[dict]],
            ): 
            # TODO NOTE Update_many() only works by using a search criteria, meaning all items will have the same data updates. Probably need to use update one at a time to update multiple items. Further research needed.
            if not data:
                return JSONResponse(status_code=400, content={"message": "No data provided"})
                                                
            completed = []
            errors = []
            for item in data:
                try:
                    # item = item.model_dump()
                    item['id'] = item.get("id")  or item.get("_id")
                    if not item.get("id"):
                        errors.append({"message": "ID field is required to update an item", "data": item if return_item_data_on_error else None})
                        continue
                    item['id'] = ObjectId(item['id'])
                    # Obtain item first.
                    row = await collection.find_one({"_id":item['id']})
                    if not row:
                        errors.append({"message": "Item not found", "data": item if return_item_data_on_error else None})
                        continue
                    try:
                        for key, value in item.items():
                            # Update row with new value
                            if hasattr(row, key):
                                try:
                                    # Check if field is read only
                                    if key in collection.Settings.endpoints_readonly_fields:
                                        log.warning(f"Field {key} is read only and should not be in the input_model. ")
                                        continue
                                except:
                                    pass
                                # NOTE Will set value to None if in json input!
                                setattr(row, key, value)
                            
                    except Exception as e:
                        log.error(e)
                        errors.append({"message": "Something went wrong. Please see the logs.", "data": item if return_item_data_on_error else None})
                        continue
                    # Callback
                    _hook = self._execute_callback(input_hook, query=CRUDQueryData(data=item, method="patch",request=request), output=row)
                    if _hook: row = _hook
                    # Update
                    try:
                        setattr(row, collection.Settings.endpoints_updated_field, utc_now())
                    except:
                        pass
                    update = await row.save()
                    row.sa
                    if update:
                        completed.append(output_model(**row.model_dump()).model_dump())
                    else:
                        errors.append({"message": "An error occurred", "data": item if return_item_data_on_error else None})
                except pymongo_errors.PyMongoError as e:
                    errors.append({"message": f"Error: {e}", "data": item if return_item_data_on_error else None})
                except Exception as e:
                    log.error(e)
                    errors.append({"message": "Something went wrong. Please see the logs.", "data": item if return_item_data_on_error else None})
            
            try:
                if not completed:
                    return JSONResponse(status_code=400, content={"message": "Failed to insert data. Check the data and try again.", "errors": errors})
                        
                _hook = self._execute_callback(output_hook, query=CRUDQueryData(data=None, method="patch",request=request), output=completed)
                if _hook: completed = _hook
                
                return {
                    "status_code": 200, "message": f"Sucessfully saved {len(completed)} {name_plural.capitalize()}, with {len(errors)} errors.", "success": completed, "errors": errors}
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})

        async def patch_one_endpoint(
                request: Request,
                data: Union[dict], 
                id: str = Path( description="ID of the item to retrieve. You can also the ID in the JSON body.", required=True ),
            ): 
            if not data:
                return JSONResponse(status_code=400, content={"message": "No data provided"})
            
            data = data if isinstance(data, list) else [data]
            
            completed = []
            errors = []
            for item in data:
                try:
                    # item = item.model_dump()
                    item['id'] = id 
                    if not item.get("id"):
                        errors.append({"message": "ID field is required to update an item", "data": item if return_item_data_on_error else None})
                        continue
                    item['id'] = ObjectId(item['id'])
                    # Obtain item first.
                    row = await collection.find_one({"_id":item['id']})
                    if not row:
                        errors.append({"message": "Item not found", "data": item})
                        continue
                    try:
                        for key, value in item.items():
                            # Update row with new value
                            if hasattr(row, key):
                                try:
                                    # Check if field is read only
                                    if key in collection.Settings.endpoints_readonly_fields:
                                        log.warning(f"Field {key} is read only and should not be in the input_model. ")
                                        continue
                                except:
                                    pass

                                setattr(row, key, value)
                            
                    except Exception as e:
                        log.error(e)
                        errors.append({"message": "Something went wrong. Please see the logs.", "data": item if return_item_data_on_error else None})
                        continue
                    # Callback
                    _hook = self._execute_callback(input_hook, query=CRUDQueryData(data=item, method="patch",request=request), output=row)
                    if _hook: row = _hook
                    # Update
                    try:
                        setattr(row, collection.Settings.endpoints_updated_field, utc_now())
                    except:
                        pass
                    update = await row.save()
                    if update:
                        completed.append(output_model(**row.model_dump()).model_dump())
                    else:
                        errors.append({"message": "An error occurred", "data": item if return_item_data_on_error else None})
                except pymongo_errors.PyMongoError as e:
                    errors.append({"message": f"Error: {e}", "data": item if return_item_data_on_error else None})
                except Exception as e:
                    log.error(e)
                    errors.append({"message": "Something went wrong. Please see the logs.", "data": item if return_item_data_on_error else None})
            
            try:
                if not completed:
                    return JSONResponse(status_code=400, content={"message": "Failed to insert data. Check the data and try again.", "errors": errors})
                _hook = self._execute_callback(output_hook, query=CRUDQueryData(data=None, method="patch",request=request), output=completed)
                if _hook: completed = _hook
                
                return {
                    "status_code": 200, "message": f"Sucessfully saved {len(completed)} {name_plural.capitalize()}, with {len(errors)} errors.", "success": completed, "errors": errors}
            
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})
                        

        #### DELETE ENDPOINTS ####
        # TODO Introduce a delete many function ? delete_many() with using ID in _ condition/query. 
        async def delete_one_endpoint(
                request: Request,
                id: str = Path( description="ID of the item to delete", required=True ),
            ):
            
            try:
                items = await collection.find_one({"_id":ObjectId(id)}) 
                _hook = self._execute_callback(input_hook, query=CRUDQueryData(data={"_id":ObjectId(id)}, method="delete",request=request), output=items)
                if _hook: items = _hook
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})
            
            if not items:
                return JSONResponse(status_code=404, content={"message": "Item not found"})   

            try:
                _hook = self._execute_callback(output_hook, query=CRUDQueryData(data={"_id":ObjectId(id)}, method="delete",request=request), output=items)
                if _hook: items = _hook
                if items:
                    _del = await items.delete()
                    if _del: 
                        return CRUDResponseModelDelete(id=id, status_code=200, message="Item deleted successfully")
                    return JSONResponse(status_code=500, content={"message": "An error occurred while deleting the item."})
            except pymongo_errors.PyMongoError as e:
                return JSONResponse(status_code=400, content={"message": f"Error: {e}"})
            except Exception as e:
                log.error(e)
                return JSONResponse(status_code=500, content={"message": "Something went wrong. Please see the logs."})
            
        #### SEARCH ENDPOINTS ####
        
        
        #### SCHEMA ENDPINT ####
        async def get_schema_endpoint(
                request: Request,
            ):
            return collection.model_json_schema(mode="validation")
        
        ###### END OF ENDPOINTS ######
        
        
        ############################################################
        ###### ADD ENDPOINTS TO ROUTER
        ############################################################
        
        for _method in method:
            
            match _method.lower():
                case "get":
                    # Add schema endpoint to get schema for collection
                    self.router.add_api_route(
                        f"{self.prefix}/{name_singluar}/schema",
                        get_schema_endpoint,
                        methods=["get"],
                        dependencies=dependencies,
                        response_model=dict,
                        tags=tags,
                        summary=f"Get schema for {name_singluar.capitalize()}",
                        description="Get the schema for the collection.",
                        include_in_schema=include_in_schema,
                        name=f"{name_singluar}_schema",
                        callbacks=completed_callbacks,
                    )
                        
                    if name_plural:
                        self.router.add_api_route(
                            f"{self.prefix}/{name_plural}",
                            get_many_endpoint,
                            methods=["get"],
                            dependencies=dependencies,
                            response_model=CRUDResponseModelGet,
                            tags=tags,
                            summary=f"Get multiple {name_plural}",
                            description=description ,
                            include_in_schema=include_in_schema,
                            name=f"{name_plural}_get",
                            callbacks=completed_callbacks,
                        )
                    if name_singluar:
                        self.router.add_api_route(
                            f"{self.prefix}/{name_singluar}"+"/{id}",
                            get_one_endpoint,
                            methods=["get"],
                            dependencies=dependencies,
                            response_model=output_model,
                            tags=tags,
                            summary=f"Get one {name_singluar.capitalize()} by ID",
                            description=description,
                            include_in_schema=include_in_schema,
                            name=f"{name_singluar}_get",
                            callbacks=completed_callbacks
                        )                    
                case "post":
                    if name_singluar:
                        self.router.add_api_route(
                            f"{self.prefix}/{name_singluar}",
                            post_endpoint,
                            methods=["post"],
                            dependencies=dependencies,
                            response_model=CRUDResponseModelPostMany,
                            tags=tags,
                            summary=f"Create one/multiple {name_singluar.capitalize()}",
                            description=description + f"\n\nUse this endpoint to create a new item in the collection. You can provide a single item or a list of items to create.\n\nSee Schemas below for the Schema for **'{input_model.__name__}'**.",
                            include_in_schema=include_in_schema,
                            name=f"{name_singluar}_post",
                            callbacks=completed_callbacks
                        )
                case "put":
                    """
                    PUT endpoint. This method is used to update a current resource with new data. The request will contain an updated version of an existing resource.

                    It is idempotent, meaning that making the same PUT request multiple times will always result in the same outcome.
                    It requires the client to know which resource to update, so the client must include the identifier for the resource.
                    If a resource with this identifier does not exist, the server can choose to create a new resource with that identifier.

                    """
                    pass
                case "patch":
                    """
                    The HTTP PATCH method is used to apply partial modifications to a resource. It's different from PUT because PUT requires you to send an entire updated entity, but with PATCH, you only send the changes.
                    """
                    if name_singluar:
                        self.router.add_api_route(
                            f"{self.prefix}/{name_singluar}"+"/{id}",
                            patch_one_endpoint,
                            methods=["patch"],
                            dependencies=dependencies,
                            response_model=CRUDResponseModelPostMany,
                            tags=tags,
                            summary=f"Update one {name_singluar.capitalize()}",
                            description=description +f"\n\nUse this endpoint to update an existing item in the collection by providing only the key-value pairs that you want to modify.\n\nSee Schemas below for the Schema for **'{input_model.__name__}'**.",
                            include_in_schema=include_in_schema,
                            name=f"{name_singluar}_update",
                            callbacks=completed_callbacks
                        )                    
                    if name_plural:
                        self.router.add_api_route(
                            f"{self.prefix}/{name_plural}",
                            patch_many_endpoint,
                            methods=["patch"],
                            dependencies=dependencies,
                            response_model=CRUDResponseModelPostMany,
                            tags=tags,
                            summary=f"Update many {name_plural.capitalize()}",
                            description=description +f"\n\nUse this endpoint to update multiple items in the collection by providing only the key-value pairs that you want to modify.\n\nSee Schemas below for the Schema for **'{input_model.__name__}'**.",
                            include_in_schema=include_in_schema,
                            name=f"{name_plural}_update",
                            callbacks=completed_callbacks
                        )    
                case "delete":
                    if name_singluar:
                        self.router.add_api_route(
                            f"{self.prefix}/{name_singluar}"+"/{id}",
                            delete_one_endpoint,
                            methods=["delete"],
                            dependencies=dependencies,
                            response_model=CRUDResponseModelDelete,
                            tags=tags,
                            summary=f"Delete one {name_singluar.capitalize()}",
                            description=description + "\n\nUse this endpoint to delete an existing item in the collection.",
                            include_in_schema=include_in_schema,
                            name=f"{name_singluar}_delete",
                            callbacks=completed_callbacks
                        )                    
                case "search":
                    """
                    Search endpoint is useful to send a MongoDB compliant JSON query to the collection and return the results.
                    """
                    pass
                case _:
                    pass
        return self # for chaining methods