from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()


class Database:
    def __init__(self, db_name):
        self.client = MongoClient(os.getenv("LOCAL_MONGODB"))
        self.db = self.client[f'{db_name}']


    def insert(self, collection, data):
        self.db[collection].insert_one(data)


    def find(self, collection, query):
        return self.db["{}".format(collection)].find(query)


    def find_one(self, collection, query):
        return self.db[collection].find_one(query)


    def update_one(self, collection, query, data):
        return self.db[collection].update_one(query, data, upsert=True).raw_result


    def remove(self, collection, query):
        self.db[collection].remove(query)