# src/core/gemini_file_search.py

"""This is the core Gemini API process to analyze, summarize the uploaded file using the Gemini API File Search Tool."""

# Import built-in modules
import asyncio
import hashlib
import re
import shutil
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
        self.display_name: Optional[str] = (
            None  # original filename stem (may contain non-ASCII)
        )
        self.upload_name: Optional[str] = None  # ASCII-safe name for API resource names

    def set_file_path(self, file_path: str) -> bool:
        """Sets the file path and prepares upload name."""
        if not file_path:
            logger.error("No file path provided.")
            return False

        self.file_path = Path(file_path)

        if not self._ensure_file_path():
            return False

        # Preserve original filename stem for display/summary purposes
        self.display_name = self.file_path.stem

        # Determine ASCII-safe name for API resource names (files/[a-z0-9-]+)
        raw_name = self.file_path.stem.lower()
        self.upload_name = re.sub(r"[^a-z0-9]+", "-", raw_name).strip("-")

        # If no valid ASCII chars remain (e.g. pure non-ASCII filename),
        # use a stable hash of the original filename so the same file always
        # maps to the same resource name, enabling cleanup on re-upload.
        if not self.upload_name:
            stable_id = hashlib.md5(self.file_path.name.encode("utf-8")).hexdigest()[:8]
            self.upload_name = f"upload-{stable_id}"

        logger.info(
            f"Selected file: {self.file_path} (Upload Name: {self.upload_name})"
        )
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
            # Create ASCII-safe temporary filename to handle non-ASCII filenames
            temp_path = (
                self.file_path.parent
                / f"upload_{uuid.uuid4().hex}{self.file_path.suffix}"
            )
            shutil.copy2(self.file_path, temp_path)

            try:
                upload_file = self.client.files.upload(
                    file=temp_path,
                    config={
                        "name": self.upload_name,
                        "display_name": self.display_name,
                    },
                )
                logger.info(f"Uploaded: {upload_file.name}")
                return upload_file.name
            finally:
                if temp_path.exists():
                    temp_path.unlink()

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

**Language rule**: Detect the primary language of the document and respond entirely in that language. Do not translate content.

**Task 1 – Summary**
Summarize the file concisely and clearly, covering the main topics and key findings.
When referencing a specific fact or section, cite the page inline using the format (p. X), where X is the page number.

**Task 2 – Key Takeaways Q&A**
End with a Q&A section of the most important takeaways from the document, in the same language as the document.

Format the entire response in clean Markdown (headings, bullet points, bold) for readability.
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
                self.save_summary(response)
        except Exception as e:
            logger.error(f"Generation failed: {e}")

    def save_summary(self, response) -> None:
        """Saves the generated summary to a markdown file."""
        if not self.display_name:
            return

        summary_dir = config.SUMMARY_DIR
        summary_dir.mkdir(exist_ok=True)

        filename = f"{self.display_name}_summary.md"
        file_path = summary_dir / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            logger.info(f"Summary saved to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
