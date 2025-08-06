from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
import json
from datetime import datetime
load_dotenv()

# MongoDB connection
uri = "mongodb+srv://alejandrocanomn:" + \
    os.getenv("DB_PASSWORD") + \
    "@cluster0.vlqder.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


def export_to_json(collection_name="products"):
    """Export all documents from MongoDB to a JSON file."""

    # MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.canadian_tire_scraper
    collection = db[collection_name]

    # all documents
    data = list(collection.find({}))

    # Convertir ObjectId y datetime a string
    def convert_document(doc):
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
            elif not isinstance(value, (str, int, float, bool, type(None), list, dict)):
                doc[key] = str(value)
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    data = [convert_document(doc) for doc in data]

    # JSON
    with open(f"output_{collection_name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    export_to_json("products")
    export_to_json("reviews")
