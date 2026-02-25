# app.py

"""This is the main application file for the Gemini File Search tool.
It provides a simple GUI for users to select a file and search for information
using the Gemini API."""

# Import built-in modules
import asyncio
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Optional

# Import custom modules
from src.config import config
from src.core.search import GeminiFileSearch
from src.utils.logger import get_app_logger

# Configure logging
logger: logging.Logger = get_app_logger()

# Validate configuration
config.validate_or_exit()


def select_file() -> Optional[Path]:
    """Opens a file dialog to select a supported file."""

    # Create a root file upload dialog window
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes("-topmost", True)  # Bring to front

    # Define supported file types for Gemini File Search
    # Based on Gemini API documentation
    filetypes: list[tuple[str, str]] = [
        (
            "Supported Files",
            "*.pdf *.doc *.docx *.ppt *.pptx *.xls *.xlsx *.csv *.txt *.md *.html *.py *.js *.java *.cpp *.json *.xml *.rtf",
        ),
        ("All Files", "*.*"),
    ]

    logger.info(msg="Opening file upload window...")

    initial_dir = config.BASE_DIR / "upload"
    if not initial_dir.exists():
        initial_dir: Path = config.BASE_DIR

    file_path_str: str = filedialog.askopenfilename(
        title="Select a file for Gemini File Search",
        filetypes=filetypes,
        initialdir=initial_dir,
    )

    # Clean up root window
    root.destroy()

    if not file_path_str:
        logger.warning(msg="No file selected.")
        return None

    return Path(file_path_str)


async def main() -> None:
    """Main function to run the Gemini File Search tool."""

    # Select file
    file_path: Path | None = select_file()
    if not file_path:
        return

    # Gemini API FileSearch Tool
    gemini_search = GeminiFileSearch()
    await gemini_search.run(file_path=str(object=file_path))


if __name__ == "__main__":
    asyncio.run(main=main())
