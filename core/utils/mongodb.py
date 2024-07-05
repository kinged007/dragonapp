from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId

# TODO Change this to use PyMongo instead of Motor - through various benchmarks, using async Motor is not actually faster than using PyMongo
# Important to save the connection so that future requests can use the same connection, decreasing the need to open and close connections and reduces the memory overhead.
# TODO implement BetterStack + Sentry logging of queries

class MongoDB():
    
    """
    MongoDB connection manager
    
    usage:
        mongo = MongoDB()
        
        async with mongo.url(self.Config.MongoDBUrl).client() as client:
        
            # Set database and collection together
            mongo.database("test").collection("tests")
            results = await mongo.query({})
            
            # Using the client directly
            results = await client['test']['tests'].find({}).to_list(None)
            
            # Using from the collection. get_X() methods are not chainable, they return the client[database][collection]
            collection = mongo.database("test").get_collection("tests")
            results = await collection.find({}).to_list(None)
        
        OR
        
        async with MongoDB().url(self.Config.MongoDBUrl).connect() as mongo:
            # mongo = MongoDB() instance
            # mongo.dbclient = AsyncIOMotorClient instance
            
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dbclient = None
        self.connect_method = None
        self.database_name = None
        self.collection_name = None
        
    @asynccontextmanager
    async def client(self):
        """
        Yields MongoDB AsyncIOMotorClient instance
        """
        await self.connect_to_mongodb()
        try:
            yield self.dbclient
            # yield self
        finally:
            await self.disconnect_from_mongodb()

    @asynccontextmanager
    async def connect(self):
        """
        Yields this MongoDB Wrapper instance
        """
        await self.connect_to_mongodb()
        try:
            yield self
        finally:
            await self.disconnect_from_mongodb()

    def url(self, mongo_db_url: str ):
        # print("Setting Connection method to URL")
        self.connect_method = "url"
        self.mongo_db_url = mongo_db_url
        return self
        
    async def connect_to_mongodb(self):
        # print("Connecting to MongoDB")
        if self.connect_method == "url":
            self.dbclient = AsyncIOMotorClient(self.mongo_db_url)
        # ... other options
            
    async def disconnect_from_mongodb(self):
        # print("Disconnecting from MongoDB")
        if self.dbclient:
            self.dbclient.close()
            self.dbclient = None
    
    def database(self, database_name):
        # print("Selecting MongoDB database")
        # if self.dbclient:
        self.database_name = database_name
            # return self.dbclient[database_name]
        return self
    
    def get_database(self, database_name = None):
        # print("Fethcing MongoDB database")
        if self.dbclient:
            if database_name:
                self.database_name = database_name
            elif not self.database_name:
                raise Exception("No database name provided")
            self.database_name = database_name
            return self.dbclient[self.database_name]
        return None
    
    def get_collection(self, collection_name = None):
        # print("Fethcing MongoDB collection")
        if self.dbclient:
            if collection_name:
                self.collection_name = collection_name
            elif not self.database_name:    
                raise Exception("No database name provided")
            elif not self.collection_name:
                raise Exception("No collection name provided")
            return self.dbclient[self.database_name][self.collection_name]
        return None
        
    def collection( self, collection_name ):
        # print("Selecting MongoDB collection")
        # if self.dbclient and self.database_name:
        self.collection_name = collection_name
            # return self.dbclient[self.database_name][collection_name]
        return self
        
    async def query(self, query):
        # print("Querying MongoDB")
        if self.dbclient and self.database_name and self.collection_name:
            return await self.dbclient[self.database_name][self.collection_name].find(query).to_list(None)
        
    async def update(self, document_id, update_data):
        # print("Updating MongoDB", update_data)
        if self.dbclient and self.database_name and self.collection_name:
            collection = self.get_collection()
            if document_id is not None:
                if not isinstance(document_id, ObjectId):
                    document_id = ObjectId(document_id)
                if '_id' in update_data:
                    del update_data['_id']
                return await collection.update_one({'_id': document_id}, {'$set': update_data})
            
    async def insert(self, update_data):
        # print("Inserting MongoDB", update_data)
        if self.dbclient and self.database_name and self.collection_name:
            collection = self.get_collection()
            return await collection.insert_one(update_data)

    async def delete(self, query):
        # print("Deleting MongoDB", query)
        if self.dbclient and self.database_name and self.collection_name:
            collection = self.get_collection()
            return await collection.delete_one(query)
        
    async def delete_by_id(self, document_id):
        if not isinstance(document_id, ObjectId):
            document_id = ObjectId(document_id)
        return await self.delete( { "_id": document_id} )

    async def find_one_by_id(self, document_id):
        if not isinstance(document_id, ObjectId):
            document_id = ObjectId(document_id)
        res = await self.query({'_id': document_id})
        if len(res) == 1:
            return res[0]
        return res