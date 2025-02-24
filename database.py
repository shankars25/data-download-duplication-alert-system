from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Fetch the MongoDB URI from the environment variables
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in the environment variables.")

# Create the MongoDB client once
client = MongoClient(MONGO_URI)
db = client.get_database("ddas1")


def get_database():
    """
    Returns the connected MongoDB database instance.
    """
    return db
