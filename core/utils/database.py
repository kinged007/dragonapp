"""
Database Manager

This utility creates and maintains connection to the main database for the application.
It creates a connection pool to allow multiple connections to it.
It primarily uses PyMongo for access to a MongoDB database, but can easily resort to a TinyDB, file based no-sql database.

This utility provides a wrapper that can be used between database types without changing the code that interacts with the database.


"""


# db.py
from pymongo import MongoClient
from core.utils.logging import logger as log
from core.utils.dict import dict_walk

# TinyDB - MongoDB alternative with MongoDB compatibility
from tinymongo import TinyMongoClient, TinyMongoDatabase, TinyMongoCollection
from tinymongo.serializers import DateTimeSerializer
from tinydb_serialization import SerializationMiddleware, Serializer
from bson.objectid import ObjectId


# from tinydb import TinyDB, JSONStorage
# from bson.json_util import dumps
# import json, io
# import os
# from datetime import datetime
# from typing import Dict, Any

# class JsonSafeStorage(JSONStorage):
#     def write(self, data: Dict[str, Dict[str, Any]]):
#         # Move the cursor to the beginning of the file just in case
#         self._handle.seek(0)

#         # Serialize the database state using the user-provided arguments
#         # serialized = json.dumps(data, **self.kwargs)
#         serialized = dumps(data, indent=4, default=str, **self.kwargs)

#         # Write the serialized data to the file
#         try:
#             self._handle.write(serialized)
#         except io.UnsupportedOperation:
#             raise IOError('Cannot write to the database. Access mode is "{0}"'.format(self._mode))

#         # Ensure the file has been writtens
#         self._handle.flush()
#         os.fsync(self._handle.fileno())

#         # Remove data that is behind the new cursor in case the file has
#         # gotten shorter
#         self._handle.truncate()

class ObjectIdSerializer(Serializer):
    OBJ_CLASS = ObjectId

    def __init__(self, *args, **kwargs):
        super(ObjectIdSerializer, self).__init__(*args, **kwargs)
        self._format = format

    def encode(self, obj):
        return str(obj)

    def decode(self, s):
        return ObjectId(s)

class DragonTinyMongoCollection(TinyMongoCollection):
    def __init__(self, table, parent=None):
        super().__init__(table, parent)

    # Hook into this method to type check the _id field.
    # for TinyDB compatibility, we need to convert the _id field to a string
    def parse_query(self, query):
        if query != {} or not query is None:
            query = dict_walk(query, lambda k,v: str(v) if isinstance(v, ObjectId) else v)
        return super().parse_query(query)
    
        
class DragonTinyMongoDatabase(TinyMongoDatabase):
    def get(self, name):
        return DragonTinyMongoCollection(name, self)
    def __getattr__(self, name):
        """Gets a new or existing collection"""
        return DragonTinyMongoCollection(name, self)

    def __getitem__(self, name):
        """Gets a new or existing collection"""
        return DragonTinyMongoCollection(name, self)
    
class DragonTinyMongoClient(TinyMongoClient):
    @property
    def _storage(self):
        serialization = SerializationMiddleware()
        serialization.register_serializer(DateTimeSerializer(), 'TinyDate')
        serialization.register_serializer(ObjectIdSerializer(), 'TinyObjectId')
        # register other custom serializers
        return serialization        
        # return JsonSafeStorage
        
    def get(self, name):
        return DragonTinyMongoDatabase(name, self._foldername, self._storage)
    
    def __getitem__(self, key):
        """Gets a new or existing database based in key"""
        # return DragonTinyMongoDatabase(key, self._foldername, self._storage)
        return self.get(key)

    def __getattr__(self, name):
        """Gets a new or existing database based in attribute"""
        # return DragonTinyMongoDatabase(name, self._foldername, self._storage)
        return self.get(name)




class Database:
    """
    Database manager class. 
    Basic usage:
        If databases have been loaded and indexes created:
            data = Database.get_collection('modules').find_one({"module_name": 'module_to_search_for'})
        If no connection previously made
    """    
    client: MongoClient = None
    tinydb_client = None
    db = None
    collection = None
    using_tinydb = False

    @classmethod
    def connect(cls, url: str, dbname: str):
        if 'tinydb' in url:
            # Using TinyDB!
            try:
                cls.using_tinydb = True
                cls.tinydb_client = DragonTinyMongoClient()
                cls.db = cls.tinydb_client.get(dbname)
            except Exception as e:
                log.error(f"Failed to connect to TinyDB: {e}")
                raise e
            return
            
        cls.client = MongoClient(url, maxPoolSize=50, minPoolSize=10)
        cls.db = cls.client[dbname]
        return True

    @classmethod
    def close(cls):
        if cls.client is not None:
            cls.client.close()

    @classmethod
    def get_collection(cls, collection_name):
        if cls.using_tinydb:
            cls.collection = cls.db.get(collection_name)
        else:        
            cls.collection = cls.db[collection_name]
        return cls.db[collection_name]
    
    
    

    # @classmethod
    # def find_one(cls, query, collection_name=None):
    #     if not collection_name and cls.collection != None:
    #         raise Exception("No collection specified.")
    #     collection = cls.get_collection(collection_name) if collection_name else cls.collection
    #     return collection.find_one(query)

    # @classmethod
    # def find(cls, query, collection_name=None):
    #     if not collection_name and cls.collection != None:
    #         raise Exception("No collection specified.")
    #     collection = cls.get_collection(collection_name) if collection_name else cls.collection
    #     return collection.find(query)

    # @classmethod
    # def insert_one(cls, document, collection_name=None):
    #     if not collection_name and cls.collection != None:
    #         raise Exception("No collection specified.")
    #     collection = cls.get_collection(collection_name) if collection_name else cls.collection
    #     return collection.insert_one(document)
    
    # @classmethod
    # def insert(cls, document, collection_name=None):
    #     return cls.insert_one(document, collection_name)

    # @classmethod
    # def insert_many(cls, documents, collection_name=None):
    #     if not collection_name and cls.collection != None:
    #         raise Exception("No collection specified.")
    #     collection = cls.get_collection(collection_name) if collection_name else cls.collection
    #     return collection.insert_many(documents)

    # @classmethod
    # def update_one(cls, query, new_values, collection_name=None):
    #     if not collection_name and cls.collection != None:
    #         raise Exception("No collection specified.")
    #     collection = cls.get_collection(collection_name) if collection_name else cls.collection
    #     return collection.update_one(query, new_values)

    # @classmethod
    # def update_many(cls, query, new_values, collection_name=None):
    #     if not collection_name and cls.collection != None:
    #         raise Exception("No collection specified.")
    #     collection = cls.get_collection(collection_name) if collection_name else cls.collection
    #     return collection.update_many(query, new_values)

    # @classmethod
    # def delete_one(cls, query, collection_name=None):
    #     if not collection_name and cls.collection != None:
    #         raise Exception("No collection specified.")
    #     collection = cls.get_collection(collection_name) if collection_name else cls.collection
    #     return collection.delete_one(query)

    # @classmethod
    # def delete_many(cls, query, collection_name=None):
    #     if not collection_name and cls.collection != None:
    #         raise Exception("No collection specified.")
    #     collection = cls.get_collection(collection_name) if collection_name else cls.collection
    #     return collection.delete_many(query)
    

    