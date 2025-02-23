from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_database():
    # Get the MongoDB URI from environment variables
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI not found in environment variables.")
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client["ddas1"]  # Access your database
    return db

# Get the database instance
db = get_database()
