"""
AI agent for file classification using OpenAI's API.

This module contains functions for interacting with an LLM to classify
a file based on its content and suggest a new filename and category.
"""
import json
import logging
import time
import random

from openai import OpenAI, OpenAIError

from . import config

# --- Prompt Templates ---

_CATEGORIES_LIST = "\n    - ".join([f'"{c}"' for c in config.CATEGORIES])

SYSTEM_PROMPT = f"""
You are an expert file organizer AI. Your task is to analyze file contents and suggest a structured, clean filename and category.

You must follow these rules:
1.  Respond ONLY with a valid JSON object. Do not add any explanatory text before or after the JSON.
2.  The `suggested_basename` must be filesystem-safe: use only lowercase letters, numbers, and underscores. No spaces or special characters.
3.  If a clear date (e.g., "Nov 9, 2025", "2025-11-09") is present in the text, include it in the `suggested_basename` in `YYYY-MM-DD` format.
4.  The `description` should be a very short, human-readable summary of the file's content.
5.  Choose a `category` from the following allowed list:
    - {_CATEGORIES_LIST}
6. Set `confidence` to your estimated probability (0.0 to 1.0) that your classification and suggested name are correct.
7.  If you cannot determine a clear category or name, use "other" and provide a generic `suggested_basename`.

The JSON response must have this exact structure:
{{
  "category": "string",
  "suggested_basename": "string",
  "confidence": "float (0.0-1.0)",
  "date": "string (YYYY-MM-DD) | null",
  "description": "string",
  "notes": "string"
}}
"""

USER_PROMPT_TEMPLATE = """
Please analyze the following file and provide your classification as a JSON object.

Original Filename: "{filename}"
File Extension: "{extension}"
Text Excerpt (first {excerpt_len} characters):
---
{text_excerpt}
---
"""


def get_openai_client() -> OpenAI:
    """
    Initializes and returns the OpenAI client.

    This function depends on the OPENAI_API_KEY being set in the environment.

    Returns:
        An instance of the OpenAI client.
        
    Raises:
        ValueError: If the API key is not configured.
    """
    config.check_api_key()  # This will raise an error if the key is missing
    return OpenAI(api_key=config.OPENAI_API_KEY)


def classify_file_with_llm(
    client: OpenAI,
    model: str,
    filename: str,
    extension: str,
    text_excerpt: str
) -> dict:
    """
    Sends file information to an LLM for classification and renaming suggestions.

    Args:
        client: The OpenAI client instance.
        model: The name of the model to use (e.g., "gpt-4o-mini").
        filename: The original name of the file.
        extension: The file's extension (e.g., ".pdf").
        text_excerpt: A snippet of the file's text content.

    Returns:
        A dictionary containing the LLM's structured response, or a default
        error dictionary if the API call or JSON parsing fails.
    """
    logging.info(f"Classifying '{filename}' with model '{model}'...")
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        filename=filename,
        extension=extension,
        text_excerpt=text_excerpt,
        excerpt_len=len(text_excerpt)
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("API returned an empty response.")
                
            # The API should return valid JSON because of response_format,
            # but we parse defensively anyway.
            parsed_json = json.loads(content)
            logging.info(f"Successfully classified '{filename}' as category '{parsed_json.get('category', 'N/A')}'.")
            return parsed_json

        except (OpenAIError, json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries - 1:
                delay = 1 * (2 ** attempt) + random.uniform(0, 1)
                logging.warning(f"Error classifying '{filename}': {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                logging.error(f"Failed to classify file '{filename}' after {max_retries} attempts: {e}")
                return {
                    "category": "error",
                    "suggested_basename": f"error_{filename.rsplit('.', 1)[0]}",
                    "confidence": 0.0,
                    "date": None,
                    "description": f"Failed to process: {e}",
                    "notes": "The AI model could not process this file.",
                }
