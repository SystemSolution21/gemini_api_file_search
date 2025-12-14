# scripts/debug/del_file_store.py
"""This script is used to delete remote file and file search stores."""

# Import built-in libraries
import logging

# Import necessary libraries
from dotenv import load_dotenv

# Import Google's library
from google import genai

# Load the environment variables
load_dotenv()

logger = logging.getLogger("del_file_store")
logging.basicConfig(level=logging.INFO)


# Initialize the client
client = genai.Client()

# Delete file
try:
    files = list(client.files.list())
    if not files:
        logger.info("No files found to delete.")

    for file in files:
        logger.info(f"{file.name=}")
        if file.name:
            logger.warning(f"{file.name=} is deleting...")
            client.files.delete(name=file.name)
            logger.info(f"{file.name=} is deleted.")

except Exception as e:
    logger.error(f"❌ Error deleting file: {e}")


# Delete file search stores
try:
    file_search_stores = list(client.file_search_stores.list())
    if not file_search_stores:
        logger.info("No file search stores found to delete.")

    for file_search_store in file_search_stores:
        logger.info(f"{file_search_store.name=}")
        logger.info(f"{file_search_store.display_name=}")
        logger.warning(f"{file_search_store.name=} is deleting...")
        client.file_search_stores.delete(
            name=str(file_search_store.name), config={"force": True}
        )
        logger.info(f"{file_search_store.name=} is deleted.")
except Exception as e:
    logger.error(f"❌ Error deleting file search store: {e}")
