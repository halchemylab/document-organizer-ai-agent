"""
Low-level filesystem and content extraction tools.

This module provides pure helper functions for interacting with the filesystem,
extracting text from different file types (PDF, images, text), and performing
file operations like renaming. These functions do not contain any AI/LLM logic.
"""


import os
import json
import logging
from pathlib import Path
from datetime import datetime

import PyPDF2
from PyPDF2.errors import PdfReadError
from PIL import Image, UnidentifiedImageError
import pytesseract
from pytesseract import TesseractNotFoundError, TesseractError
import docx
from docx.opc.exceptions import PackageNotFoundError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def list_files(directory: str) -> list[dict]:
    """
    Lists all files in a given directory (non-recursively).

    Args:
        directory: The absolute path to the directory to scan.

    Returns:
        A list of dictionaries, where each dictionary represents a file
        and contains its path, name, extension, size, and modification time.
        Hidden files (starting with '.') are ignored.
    """
    logging.info(f"Scanning directory: {directory}")
    files = []
    dir_path = Path(directory)
    if not dir_path.is_dir():
        logging.error(f"Directory not found: {directory}")
        return []

    for item in dir_path.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            try:
                stat = item.stat()
                files.append({
                    "path": str(item.resolve()),
                    "name": item.name,
                    "ext": item.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except (FileNotFoundError, PermissionError, OSError) as e:
                logging.warning(f"Could not access file {item.name}: {e}")

    logging.info(f"Found {len(files)} files in {directory}.")
    return files


def extract_text_from_pdf(path: str) -> str:
    """
    Extracts text content from a PDF file.

    Args:
        path: The path to the PDF file.

    Returns:
        The concatenated text from all pages, or an empty string if
        extraction fails or the file is encrypted.
    """
    logging.info(f"Extracting text from PDF: {path}")
    text = ""
    try:
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if reader.is_encrypted:
                logging.warning(f"PDF is encrypted, cannot extract text: {path}")
                return ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                else:
                    logging.debug(f"No text found on page {i+1} of {path}")
    except (PdfReadError, OSError) as e:
        logging.error(f"Failed to read or parse PDF {path}: {e}")
    return text


def extract_text_from_docx(path: str) -> str:
    """
    Extracts text content from a Microsoft Word (.docx) file.

    Args:
        path: The path to the .docx file.

    Returns:
        The concatenated text from all paragraphs, or an empty string if
        extraction fails.
    """
    logging.info(f"Extracting text from DOCX: {path}")
    text = ""
    try:
        doc = docx.Document(path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except (PackageNotFoundError, ValueError, OSError) as e:
        logging.error(f"Failed to read or parse DOCX {path}: {e}")
    return text


def extract_text_from_image(path: str) -> str:
    """
    Extracts text from an image file using Optical Character Recognition (OCR).

    Note: This function requires the Tesseract OCR engine to be installed and
    available in the system's PATH.

    Args:
        path: The path to the image file.

    Returns:
        The recognized text, or an empty string if OCR fails.
    """
    logging.info(f"Extracting text from image (OCR): {path}")
    try:
        with Image.open(path) as img:
            text = pytesseract.image_to_string(img)
            return text
    except TesseractNotFoundError:
        logging.error("Tesseract is not installed or not in your PATH. Cannot perform OCR.")
        # Re-raise to make it a fatal error for image processing if Tesseract is missing
        raise
    except (TesseractError, UnidentifiedImageError, OSError) as e:
        logging.error(f"Failed to perform OCR on image {path}: {e}")
    return ""


def read_text_file(path: str, max_chars: int = 10000) -> str:
    """
    Reads content from a plain text file.

    Args:
        path: The path to the text file.
        max_chars: The maximum number of characters to return.

    Returns:
        The content of the file, truncated to `max_chars`.
    """
    logging.info(f"Reading text file: {path}")
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(max_chars)
        return content
    except (OSError, UnicodeDecodeError) as e:
        logging.error(f"Failed to read text file {path}: {e}")
    return ""


def rename_file(old_path: str, new_path: str) -> str:
    """
    Renames a file, automatically handling name collisions.

    If the target `new_path` already exists, a numeric suffix (e.g., '_1', '_2')
    is appended to the filename before the extension.

    Args:
        old_path: The current path of the file.
        new_path: The desired new path of the file.

    Returns:
        The actual final path of the renamed file.
    """
    old_p = Path(old_path)
    new_p = Path(new_path)

    if not new_p.parent.exists():
        logging.info(f"Creating directory for renamed file: {new_p.parent}")
        new_p.parent.mkdir(parents=True, exist_ok=True)

    final_path = new_p
    counter = 1
    while final_path.exists():
        final_path = new_p.parent / f"{new_p.stem}_{counter}{new_p.suffix}"
        counter += 1

    try:
        old_p.rename(final_path)
        logging.info(f"Renamed '{old_p.name}' to '{final_path.name}'")
        return str(final_path.resolve())
    except OSError as e:
        logging.error(f"Failed to rename file from {old_path} to {final_path}: {e}")
        return old_path


def write_metadata_json(directory: str, records: list[dict], filename: str = "metadata.json") -> str:
    """
    Writes a list of records to a JSON file in a pretty-printed format.

    Args:
        directory: The directory where the JSON file will be saved.
        records: A list of dictionaries to serialize into JSON.
        filename: The name of the output file.

    Returns:
        The full path to the created metadata file.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        
    output_path = dir_path / filename
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=4)
        logging.info(f"Successfully wrote metadata to {output_path}")
        return str(output_path.resolve())
    except OSError as e:
        logging.error(f"Failed to write metadata file at {output_path}: {e}")
        return ""