import pymongo
from pymongo import MongoClient

try:
    uri= 'mongodb://localhost:27017'
    client = MongoClient(uri)

    database = client['test_database']
    collection = database['test_collection']

    # start example code

    collection.insert_one()

    # end example code

    client.close()
except Exception as e:
    raise Exception("hata oluştu: ", e)