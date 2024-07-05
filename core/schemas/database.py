"""
DatabaseMongoBaseModel

This is the base class for all database models. It provides the basic structure for all database models to inherit from.
Based on Pydantic BaseModel itself, it can use all of the Pydantic features and validations.
Depending on the configuration passed to it, it will utilise PyMongo or SQLModel to interact with the database.

"""

from typing_extensions import Literal, TypeAlias
from pydantic import BaseModel as PydanticBaseModel, Field, validator, VERSION, root_validator
from pydantic.json_schema import GenerateJsonSchema
# from sqlmodel import SQLModel, Field # We use Field from SQLModel instead of Pydantic as a standard
from typing import Optional, Any, TYPE_CHECKING, Type
from datetime import datetime, timezone
from bson import DBRef, ObjectId
from bson.errors import InvalidId
from core.config import settings
from core.utils.logging import logger as log
from core.utils.database import Database

IS_PYDANTIC_V2 = int(VERSION.split(".")[0]) >= 2
if IS_PYDANTIC_V2:
    from pydantic import (
        GetCoreSchemaHandler,
        GetJsonSchemaHandler,
        TypeAdapter,
    )
    from pydantic.json_schema import JsonSchemaValue
    from pydantic_core import CoreSchema, core_schema
    from pydantic_core.core_schema import (
        ValidationInfo,
        simple_ser_schema,
        str_schema,
    )
else:
    from pydantic.fields import ModelField  # type: ignore
    from pydantic.json import ENCODERS_BY_TYPE

class PydanticObjectId(ObjectId):
    """
    Object Id field. Compatible with Pydantic.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    if IS_PYDANTIC_V2:

        @classmethod
        def validate(cls, v, _: ValidationInfo):
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            try:
                return PydanticObjectId(v)
            except (InvalidId, TypeError):
                raise ValueError("Id must be of type PydanticObjectId")

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> CoreSchema:  # type: ignore
            return core_schema.json_or_python_schema(
                python_schema=core_schema.with_info_plain_validator_function(
                    cls.validate
                ),
                json_schema=str_schema(),
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda instance: str(instance)
                ),
            )

        @classmethod
        def __get_pydantic_json_schema__(
            cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler  # type: ignore
        ) -> JsonSchemaValue:
            json_schema = handler(schema)
            json_schema.update(
                type="string",
                example="5eb7cf5a86d9755df3a6c593",
            )
            return json_schema

    else:

        @classmethod
        def validate(cls, v):
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            try:
                return PydanticObjectId(v)
            except InvalidId:
                raise TypeError("Id must be of type PydanticObjectId")

        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema.update(
                type="string",
                example="5eb7cf5a86d9755df3a6c593",
            )

if not IS_PYDANTIC_V2:
    ENCODERS_BY_TYPE[
        PydanticObjectId
    ] = str  # it is a workaround to force pydantic make json schema for this field



class DatabaseMongoBaseModelMeta(type(PydanticBaseModel)):
    """
    Validate that the model has a 'Settings' class with a 'name' attribute.
    """
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if 'Settings' not in attrs or not hasattr(attrs['Settings'], 'name'):
            raise TypeError(f"{name} must have a Settings class with a 'name' attribute.")
        
        return cls  
    
    # TODO id field is automatically added
    # created_on field is automatically added
    # updated_on field is automatically added
    # created_by field is automatically added
    
    # class Settings:
    #     # define database settings such as 'name' = collection name saved in the database.
    #     name = "my_db_collection"
    #     # Name must be defined so it can be initialized and indexes applied.
    #     # Indexes: List of indexes you want to apply to this collection. Uses PyMongo syntax. Will be applied using create_index()
    #     # https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#pymongo.collection.Collection.create_index
    #     # Pass these parameters as a dict
    #     # PARAMETERS:
    #     #     keys (_IndexKeyHint) – a single key or a list of (key, direction) pairs specifying the index to create
    #     #     comment (Optional[Any]) – A user-provided comment to attach to this command.
    #     #     kwargs (Any) – any additional index creation options (see the above list) should be passed as keyword arguments.
    #     indexes = [
    #         {
    #             "keys": [
    #                 ("domain", pymongo.ASCENDING),
    #             ],
    #             "unique": True
    #         },
    #         # ...
    #     ]


class DatabaseMongoBaseModel(PydanticBaseModel, metaclass=DatabaseMongoBaseModelMeta):
    """
    Base class for all database models.
    The model that extends this class will be the database Collection, and can be used to interact with the database.
    """    
    # TODO id field is automatically added if mongodb is used, else we should add it.
    # id: Optional[str] = PydanticField(alias='_id', default_factory=lambda: str(ObjectId()))
    id: Optional[PydanticObjectId] = Field(
        description="MongoDB document ObjectID", default=None, # default_factory=lambda: PydanticObjectId() #
    )
    created_on: Optional[datetime] = Field(
        description="The date and time the document was created", default_factory=lambda: datetime.now(timezone.utc),
        json_schema_extra={"readOnly": True}
    )
    updated_on: Optional[datetime] = Field(
        description="The date and time the document was last updated", default_factory=lambda: datetime.now(timezone.utc),
        json_schema_extra={"readOnly": True}
    )
    # TODO Add User fields for created_by, updated_by, deleted_by
    
    class Settings:
        name = "my_db_collection"        

    @classmethod
    def collection_name(cls):
        return cls.Settings.name
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        json_schema_extra = {
            'type': 'database_ref',
        }
        
        # fields = {"id": "_id"} # Deprecated pydantic V2
    
    @root_validator(pre=True)
    def set_created_on(cls, values):
        if "created_on" not in values or values["created_on"] is None:
            values["created_on"] = datetime.now(timezone.utc)
        return values

    @root_validator(pre=True)
    def set_updated_on(cls, values):
        values["updated_on"] = datetime.now(timezone.utc)
        return values    
    
    # @validator('id', pre=True, always=True)
    # def set_id(cls, v):
    #     return v or str(ObjectId())
    #     # _id = getattr(cls, '_id', getattr(cls, 'id', None))
        # print("ID",_id)
        # return str(_id) if _id else str(ObjectId())
    
    # @property
    # def _id(self):
    #     return getattr(self, '_id', None) or str(ObjectId())
        # return self.id
    
    def __init__(self, **data):
        
        # Convert all naive datetime objects in data to aware datetime objects
        for key, value in data.items():
            if isinstance(value, datetime) and value.tzinfo is None:
                print(value)
                data[key] = value.replace(tzinfo=timezone.utc)
        super().__init__(**data)
        if not data.get('_id', None) and not self.id:
            self.id = PydanticObjectId()
        if not self.id and data.get('_id', None):
            self.id = data['_id']
        if data.get('_id', None) and self.id != data['_id']:
            self.id = data['_id']
        
    def model_dump(self, *, mode: str = 'python', include: set[int] | set[str] | dict[int, Any] | dict[str, Any] | None = None, exclude: set[int] | set[str] | dict[int, Any] | dict[str, Any] | None = None, by_alias: bool = False, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, round_trip: bool = False, warnings: bool = True) -> dict[str, Any]:
        """
        Return the model as a dictionary.
        """
        try:
            _dict = super().model_dump(mode=mode, include=include, exclude=exclude, by_alias=by_alias, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults, exclude_none=exclude_none, round_trip=round_trip, warnings=warnings)
            if Database.using_tinydb:
                _dict['_id'] = str(_dict['id'])
            else:
                _dict['_id'] = PydanticObjectId(_dict['id'])
            _dict.pop('id', None)
            return _dict
        except Exception as e:
            log.error(f"Failed to dump model: {e}")
            return None
        return 
    
    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: Any = None,
        exclude: Any = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> str:
        """Usage docs: https://docs.pydantic.dev/2.5/concepts/serialization/#modelmodel_dump_json

        Generates a JSON representation of the model using Pydantic's `to_json` method.
        Automatically re-assigns id/_id field to be used with Pymongo / TinyDB

        Args:
            indent: Indentation to use in the JSON output. If None is passed, the output will be compact.
            include: Field(s) to include in the JSON output. Can take either a string or set of strings.
            exclude: Field(s) to exclude from the JSON output. Can take either a string or set of strings.
            by_alias: Whether to serialize using field aliases.
            exclude_unset: Whether to exclude fields that have not been explicitly set.
            exclude_defaults: Whether to exclude fields that have the default value.
            exclude_none: Whether to exclude fields that have a value of `None`.
            round_trip: Whether to use serialization/deserialization between JSON and class instance.
            warnings: Whether to show any warnings that occurred during serialization.

        Returns:
            A JSON string representation of the model.
        """
        try:
            import json
            _dict = json.loads(super().model_dump_json(
                indent = indent,
                include = include,
                exclude = exclude,
                by_alias = by_alias,
                exclude_unset = exclude_unset,
                exclude_defaults = exclude_defaults,
                exclude_none = exclude_none,
                round_trip = round_trip,
                warnings = warnings,
            ))
            if Database.using_tinydb:
                _dict['_id'] = str(_dict['id'])
            else:
                _dict['_id'] = PydanticObjectId(_dict['id'])
            _dict.pop('id', None)
            return _dict
        except Exception as e:
            log.error(f"Failed to dump model: {e}")
            return None
        return 

    @classmethod
    def model_json_schema(
        cls,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Generates a JSON schema for a model class.

        Args:
            by_alias: Whether to use attribute aliases or not.
            ref_template: The reference template.
            schema_generator: To override the logic used to generate the JSON schema, as a subclass of
                `GenerateJsonSchema` with your desired modifications
            mode: The mode in which to generate the schema.

        Returns:
            The JSON schema for the given model class.
        """    
        # json_schema_extra = cls.Config.json_schema_extra.copy()
        # json_schema_extra['collection_name'] = cls.collection_name()
        # cls.Config.json_schema_extra.update({'collection_name': cls.collection_name()})
        # Move metadata fields to end of schema
        metadata_fields = {}
        json_schema = super().model_json_schema(*args, **kwargs)
        properties = json_schema.get('properties', {})

        for field in ['created_on', 'updated_on', 'created_by', 'updated_by', 'deleted_by']:
            if field in properties:
                metadata_fields[field] = properties.pop(field)

        # Add the metadata fields back to the properties dictionary
        properties.update(metadata_fields)

        return json_schema    
    
    # @classmethod
    # def from_dict(cls, data: dict):
    #     return cls(**data)
    
    # def to_dict(self):
    #     return self.model_dump()

    # def to_mongo_dict(self):
    #     # Exclude the 'id' field for MongoDB as _id is generally auto-generated
    #     data = self.model_dump()
    #     data.pop('id', None)
    #     return data

    # def save(self): # TODO implement save/delete/update methods from the basemodel, allowing database interaction from the model
    #     """
    #     Save the model to the database
    #     """
    #     pass

    # def delete(self):
    #     """
    #     Delete the model from the database
    #     """
    #     pass
    
    