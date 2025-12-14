# src/core/gemini_file_search.py

"""This is the core Gemini API process to analyze, summarize the uploaded file using the Gemini API File Search Tool."""

# Import built-in modules
import asyncio
import re
import uuid
from pathlib import Path
from typing import Optional

# Import third-party modules
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import custom modules
from src.config import config
from src.utils.logger import get_app_logger

# Configure logging
logger = get_app_logger()

# Load env
load_dotenv()


class GeminiFileSearch:
    def __init__(self):
        self.model_id = config.GEMINI_MODEL

        # Initialize Client
        self.client = genai.Client()

        # Placeholders for file info
        self.file_path: Optional[Path] = None
        self.upload_name: Optional[str] = None

    def set_file_path(self, file_path: str) -> bool:
        """Sets the file path and prepares upload name."""
        if not file_path:
            logger.error("No file path provided.")
            return False

        self.file_path = Path(file_path)

        if not self._ensure_file_path():
            return False

        # Determine internal name (lowercase, sanitized) - used for generic ID generation
        # We strip non-alphanumeric characters to ensure compliance with resource name requirements
        # Resource names typically follow: files/[a-z0-9-]+
        raw_name = self.file_path.name.lower().rsplit(".", 1)[0]
        self.upload_name = re.sub(r"[^a-z0-9]+", "-", raw_name).strip("-")

        # fallback to random ID if no valid name
        if not self.upload_name:
            self.upload_name = f"upload-{uuid.uuid4().hex[:8]}"

        logger.info(f"Selected file: {self.file_path} (ID: {self.upload_name})")
        return True

    def _ensure_file_path(self) -> bool:
        """Ensures the file path exists."""
        if not self.file_path or not self.file_path.exists():
            logger.error(f"Local file not found at {self.file_path}")
            return False
        return True

    def upload_file_search(self) -> Optional[str]:
        """Uploads the file to Gemini."""
        if not self.upload_name or not self.file_path:
            return None

        resource_name = f"files/{self.upload_name}"

        # Check and cleanup existing
        try:
            file = self.client.files.get(name=resource_name)
            if file.name == resource_name:
                logger.info(f"{self.upload_name} already exists! Deleting...")
                self.client.files.delete(name=resource_name)
                logger.info(f"{self.upload_name} deleted!")
        except Exception as e:
            logger.debug(f"File lookup failed (likely doesn't exist): {e}")

        # Upload
        logger.info(f"Uploading {self.file_path.name}...")
        try:
            upload_file = self.client.files.upload(
                file=self.file_path, config={"name": self.upload_name}
            )
            logger.info(f"Uploaded: {upload_file.name}")
            return upload_file.name
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

    def create_file_search_store(self) -> Optional[str]:
        """Creates a file search store."""
        if not self.upload_name:
            return None

        # Cleanup existing stores with same display name
        try:
            for store in self.client.file_search_stores.list():
                if store.display_name == self.upload_name:
                    logger.info(f"Found existing store {store.name}. Deleting...")
                    self.client.file_search_stores.delete(
                        name=str(store.name), config={"force": True}
                    )
                    logger.info(f"Deleted store: {store.name}")
        except Exception as e:
            logger.error(f"Error managing existing stores: {e}")
            return None

        # Create new
        logger.info("Creating File Search store...")
        try:
            store = self.client.file_search_stores.create(
                config={"display_name": self.upload_name}
            )
            logger.info(f"Created store: {store.name}")
            return store.name
        except Exception as e:
            logger.error(f"Store creation failed: {e}")
            return None

    async def run(self, file_path: str):
        """Runs the Gemini File Search process."""
        # 1. Set File
        if not self.set_file_path(file_path):
            return

        # 2. Upload
        uploaded_file_name = self.upload_file_search()
        if not uploaded_file_name:
            return

        # 3. Create Store
        store_name = self.create_file_search_store()
        if not store_name:
            return

        # 4. Import File
        logger.info("Importing file to store...")
        try:
            operation = self.client.file_search_stores.import_file(
                file_search_store_name=store_name,
                file_name=uploaded_file_name,
                config={
                    "custom_metadata": [
                        {"key": "filename", "string_value": self.upload_name},
                    ]
                },
            )

            # Polling
            while not operation.done:
                await asyncio.sleep(2)
                operation = self.client.operations.get(operation)
                print(".", end="", flush=True)
            print()  # Newline
            logger.info("Import complete.")

        except Exception as e:
            logger.error(f"Import failed: {e}")
            return

        # 5. Generate Content
        logger.info("Generating content...")
        prompt = """You are a helpful assistant. You have access to the provided files.
Summarize the file based on the information in these files.
Keep the summary concise and to the point.
When citing sources, use the format (p. X) for page references, where X is the page number.
Format your responses in a clear, readable style that works well with markdown rendering.
Finally make key takeaways Q&A from the file.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[store_name],
                                metadata_filter=f"filename={self.upload_name}",
                            )
                        )
                    ]
                ),
            )

            # Save summary
            if response.text:
                self.save_summary(response.text)
        except Exception as e:
            logger.error(f"Generation failed: {e}")

    def save_summary(self, content: str):
        """Saves the generated summary to a markdown file."""
        if not self.upload_name:
            return

        summary_dir = config.SUMMARY_DIR
        summary_dir.mkdir(exist_ok=True)

        filename = f"{self.upload_name}_summary.md"
        file_path = summary_dir / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Summary saved to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
