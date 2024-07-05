from bson import ObjectId


# def mongo_to_dict(obj):
#     if isinstance(obj, str):
#         return obj

#     return_data = []

#     if isinstance(obj, Document):
#         return_data.append(("id", str(obj.id)))
    
#     for field_name in obj:
#         if field_name == "id":
#             continue

#         data = obj[field_name]

#         if isinstance(data, ObjectId):
#             return_data.append((field_name, str(data)))
#         elif isinstance(data, list):
#             return_data.append((field_name, [mongo_to_dict(item) for item in data]))
#         elif isinstance(data, dict):
#             return_data.append((field_name, mongo_to_dict(data)))
#         else:
#             return_data.append((field_name, data))

#     return dict(return_data)

import os
from pymongo import MongoClient
from core.config import settings

class MongoUtil:
    def __init__(self, url=None):
        if not url:
            url = settings.MONGODB_URI
        if not url:
            raise Exception("No database URL provided.")
        self.client = MongoClient(url)
        self.db = self.client[settings.DATABASE_NAME]

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def find_one(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.find_one(query)

    def find(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.find(query)

    def insert_one(self, collection_name, document):
        collection = self.get_collection(collection_name)
        return collection.insert_one(document)

    def insert_many(self, collection_name, documents):
        collection = self.get_collection(collection_name)
        return collection.insert_many(documents)

    def update_one(self, collection_name, query, new_values):
        collection = self.get_collection(collection_name)
        return collection.update_one(query, new_values)

    def update_many(self, collection_name, query, new_values):
        collection = self.get_collection(collection_name)
        return collection.update_many(query, new_values)

    def delete_one(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.delete_one(query)

    def delete_many(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.delete_many(query)
    

    