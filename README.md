# AI Document Organizer

This project is a Python application with a Streamlit UI that uses an AI agent to help you organize a folder of local documents. It scans files (PDFs, images, text), uses an OpenAI model to classify them and suggest new, clean filenames, and then allows you to apply these changes.

## Features

-   **Web-based UI**: Simple, clean interface powered by Streamlit.
-   **Folder Scanning**: Select any local directory to organize.
-   **Multi-Format Support**: Extracts content from:
    -   PDFs (`.pdf`)
    -   Images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.heic`) using OCR.
    -   Plain Text (`.txt`).
-   **AI-Powered Classification**: Sends file content to an OpenAI model (e.g., `gpt-4o-mini`) to intelligently categorize each file and propose a new, consistent filename.
-   **Safe Dry-Run Mode**: First, it always presents a "plan" of proposed renames without changing anything on your disk.
-   **One-Click Execution**: Apply all proposed renames with a single button click.
-   **Metadata Logging**: Saves a `metadata.json` file in the organized folder, detailing every change, the AI's classification, and other useful information.
-   **CLI Support**: Includes a command-line interface for headless operation.

## Requirements

-   Python 3.10+
-   An OpenAI API Key.
-   **Tesseract OCR Engine**: This tool requires the Tesseract binary to be installed on your system for extracting text from images.
    -   **Windows**: Download and run the installer from the official [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) page. Make sure to add the Tesseract installation directory to your system's `PATH`.
    -   **macOS**: `brew install tesseract`
    -   **Linux (Debian/Ubuntu)**: `sudo apt update && sudo apt install tesseract-ocr`

## Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create and Activate a Virtual Environment**:
    ```bash
    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate

    # For Windows
    python -m venv .venv
    .\.venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Your OpenAI API Key**:
    -   Copy the example environment file:
        ```bash
        # For macOS/Linux
        cp .env.example .env

        # For Windows
        copy .env.example .env
        ```
    -   Open the `.env` file and add your OpenAI API key:
        ```
        OPENAI_API_KEY="sk-..."
        ```

## How to Run

Make sure your virtual environment is activated before running.

### Streamlit UI (Recommended)

Run the following command from the project's root directory:

```bash
streamlit run src/streamlit_app.py
```

Navigate to the URL provided by Streamlit (usually `http://localhost:8501`) in your browser.

### Command-Line Interface (CLI)

You can also run the organizer from the command line.

**Dry Run (show a plan but don't apply it):**

```bash
python -m src.cli --directory "/path/to/your/documents"
```

**Apply Renames:**

```bash
python -m src.cli --directory "/path/to/your/documents" --apply
```

## `metadata.json`

After applying a plan, a `metadata.json` file is created in the target directory. It contains a list of records, one for each file processed, with the following structure:

```json
{
    "old_path": "C:\\Users\\user\\docs\\IMG_1234.PNG",
    "old_name": "IMG_1234.PNG",
    "final_new_name": "receipt_2025-11-15_starbucks.png",
    "final_new_path": "C:\\Users\\user\\docs\\receipt_2025-11-15_starbucks.png",
    "category": "receipt",
    "confidence": 0.9,
    "date": "2025-11-15",
    "description": "Starbucks coffee receipt",
    "notes": "The total amount was $5.75."
}
```

## ⚠️ Warnings

-   **Always use the "Dry Run" feature first** to review the proposed changes before applying them.
-   It is highly recommended to **test the application on a sample folder** of documents before running it on important files.
-   The quality of the AI's suggestions depends on the model and the clarity of the text within the documents. OCR is not perfect and may fail on blurry or complex images.
