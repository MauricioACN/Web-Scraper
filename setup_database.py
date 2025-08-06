import json
import os
import pymongo
from datetime import datetime
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
uri = "mongodb+srv://alejandrocanomn:" + \
    os.getenv("DB_PASSWORD") + \
    "@cluster0.vlqder.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


def load_data_simple():
    """Simple MongoDB loader - separate collections"""

    # Connect to MongoDB
    client = MongoClient(
        uri, server_api=ServerApi('1'))
    db = client.canadian_tire_scraper

    print("🚀 Loading data to MongoDB (Simple approach)...")

    # 1. Load Products
    with open("productos_cleaned.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    # Clear existing data
    db.products.delete_many({})

    # Insert products
    db.products.insert_many(products)
    print(f"✅ Loaded {len(products)} products")

    # 2. Load Reviews (if exists)
    try:
        with open("product_reviews.json", "r", encoding="utf-8") as f:
            reviews = json.load(f)

        # Clear existing reviews
        db.reviews.delete_many({})

        # Insert reviews
        if reviews:
            db.reviews.insert_many(reviews)
            print(f"✅ Loaded {len(reviews)} reviews")
    except FileNotFoundError:
        print("⚠️ No reviews file found, skipping reviews")

    # 3. Simple indexes
    db.products.create_index("product_id", unique=True)
    db.reviews.create_index("product_id")
    db.reviews.create_index("reviewer")

    print("✅ Simple indexes created")
    print("🎉 Data loading complete!")

    # Show summary
    print(f"\n📊 Summary:")
    print(f"   Products: {db.products.count_documents({})}")
    print(f"   Reviews: {db.reviews.count_documents({})}")

    client.close()


if __name__ == "__main__":
    load_data_simple()
