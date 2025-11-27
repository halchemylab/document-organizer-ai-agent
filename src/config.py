"""
Configuration loader for the AI Document Organizer.

This module handles loading environment variables from a .env file
and provides centralized access to configuration values like the
OpenAI API key and default model name.
"""

import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# --- OpenAI Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-4o-mini"

# A list of image extensions that the application will attempt to OCR.
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".heic", ".webp"]

# A list of text file extensions that the application will read.
TEXT_EXTENSIONS = [".txt", ".md", ".rtf", ".docx"]

# Maximum characters to extract from a file to avoid overly long prompts.
MAX_CHARS_PER_FILE = 8000

# List of allowed categories for file classification
CATEGORIES = [
    "insurance",
    "ticket",
    "vote",
    "legal",
    "personal",
    "screenshot",
    "receipt",
    "finance",
    "work",
    "invoice",
    "manual",
    "medical",
    "travel",
    "education",
    "other",
]

# Perform a basic check for the API key on import
def check_api_key():
    """Checks for the presence of the OpenAI API key and raises an error if not found."""
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Please create a .env file with your key, "
            "or set the environment variable directly."
        )