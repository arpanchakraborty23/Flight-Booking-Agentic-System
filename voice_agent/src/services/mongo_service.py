import logging

from dotenv import load_dotenv
from pymongo import MongoClient, errors

# Configure logging
logger = logging.getLogger(__name__)
load_dotenv()

class MongoDBValidation:
    """Single Class Validate MongoDB Credentials"""

    @staticmethod
    def mongo_credentials(url: str, db: str, collection: str):
        """
        Validate MongoDB connection, database, and collection.

        Args:
            url (str): MongoDB connection string
            db (str): Database name
            collection (str): Collection name

        Returns:
            tuple: (MongoClient, collection_name)
        """
        client = None
        try:
            client = MongoClient(url, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")  # Test connection

            database = client[db]
            if collection not in database.list_collection_names():
                logger.warning(
                    f"✅ Connected to MongoDB, but collection '{collection}' not found in '{db}'."
                )
            else:
                logger.info(f"✅ MongoDB credentials valid. Connected to '{db}.{collection}'.")

            return client, database[collection]

        except errors.OperationFailure as e:
            logger.error(f"❌ MongoDB Authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ MongoDB Connection error: {e}")
            raise




class MongoServices:
    """Responsibility: Manage MongoDB Connection"""

    def __init__(self, url: str, db: str, collection: str):
        self.url = url
        self.db = db
        self.collection_name = collection
        self.client = None
        self.collection = None

    def connect(self):
        self.client, self.collection = MongoDBValidation.mongo_credentials(
            url=self.url, db=self.db, collection=self.collection_name
        )
        return self.collection

    def insert_one(self, document: dict):
        if self.collection is None:
            self.connect()
        assert self.collection is not None
        return self.collection.insert_one(document)

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.collection = None
            logger.info("🧹 MongoDB connection closed.")
