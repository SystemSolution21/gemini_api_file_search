# Gemini API File Search

A Python application that leverages Google's Gemini API to process, analyze, and summarize local files using the File Search capability.

## Features

- **User-Friendly Interface**: Select files easily using a standard system file dialog.
- **Automated Processing**: Handles the entire pipeline from upload to content generation.
- **Smart Resource Management**: Automatically handles cleanup of old files and vector stores on the Gemini API side.
- **Local Summaries**: Saves the generated summary and Q&A as Markdown files in a local `summary/` directory.

## How It Works & Resource Management

Working with the Gemini API File Search involves specific constraints:

1. **File Retention**: Files uploaded to the Gemini API are automatically deleted after **2 days**.
2. **Store Persistence**: "File Search Stores" (vector stores) persist until manually deleted and can accumulate over time if not managed.

**This application addresses these constraints by implementing an active cleanup lifecycle:**

1. **Selection**: When you select a file (e.g., `document.pdf`), the app generates a unique but consistent ID based on the filename.
2. **Cleanup**: Before uploading, it checks if a File or File Search Store with that specific ID already exists.
    - If found, it **deletes** the old Store and File to ensure you are always working with the fresh version and to prevent cluttering your Google Cloud project with stale data.
3. **Creation**: It then uploads the new file and creates a fresh File Search Store.
4. **Generation**: Finally, it prompts Gemini to summarize the document and cite sources.

## Setup

1. **Environment Variables**: Change the `.env.example` file to `.env` and fill in the values:

    ```env
    GOOGLE_API_KEY=your_api_key_here

    # Gemini model configurations
    GEMINI_MODEL=gemini-2.5-flash or your preferred model
    GEMINI_TEMPERATURE=1
    GEMINI_TOP_P=0.95
    GEMINI_TOP_K=64
    GEMINI_MAX_OUTPUT_TOKENS=8192

    # File Upload
    MAX_FILE_SIZE_MB=20
    UPLOAD_TIMEOUT=180
    ```

2. **Dependencies**: Install required packages using uv:

    ```pwsh
    uv sync
    ```

## Usage

Run the application wrapper:

```pwsh
python app.py
```

1. A file dialog will open.
2. Select the file you want to analyze.
3. Monitor the console for progress (uploading, indexing, generating).
4. Find your summary in the `summary/` folder.
