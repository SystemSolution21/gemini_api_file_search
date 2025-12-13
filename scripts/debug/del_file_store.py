# scripts/debug/del_file_store.py
"""This script is used to delete file store."""

# Import built-in libraries
from pathlib import Path

# Import necessary libraries
from dotenv import load_dotenv

# Import Google's library
from google import genai

# Load the environment variables
load_dotenv()

# Initialize the client
client = genai.Client()


# Upload file configuration
base_dir: Path = Path(__file__).parent.parent.resolve()
file_dir: Path = base_dir / "upload"
file_name: str = "ticket-to-ride.pdf"
file_path: Path = file_dir / file_name
upload_file_name: str = file_name.lower().removesuffix(".pdf")

# Check uploaded file
try:
    file = client.files.get(name=upload_file_name)
    get_file_name = (
        str(file.name).lower().removeprefix("files/")
    )  # remove prefix 'files/' from returned full file path name from gemini api
    if get_file_name == upload_file_name:
        print(f"{upload_file_name} is already exists!")
        client.files.delete(name=get_file_name)
        print(f"{get_file_name} is deleted")

except Exception as e:
    print(e)
    exit(1)


# Delete file search stores
try:
    file_search_stores = client.file_search_stores.list()
    for file_search_store in file_search_stores:
        print(f"{file_search_store.name=}")
        print(f"{file_search_store.display_name=}")
        client.file_search_stores.delete(
            name=str(file_search_store.name), config={"force": True}
        )
        print(f"{file_search_store.name=} is deleted")
except Exception as e:
    print(e)
    exit(1)
