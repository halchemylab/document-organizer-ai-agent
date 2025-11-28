"""
Orchestration logic for the document organization process.

This module ties together the file tools and the LLM agent to build
and apply an organization plan for a directory.
"""
import logging
import concurrent.futures
from pathlib import Path

from . import tools, llm_agent, config

def _process_file(file_info: dict, directory: str, model: str, client) -> dict | None:
    """
    Helper function to process a single file: extract text, classify, and create a plan entry.
    """
    text_excerpt = ""
    file_path = file_info["path"]
    file_ext = file_info["ext"]

    try:
        if file_ext == ".pdf":
            text_excerpt = tools.extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            text_excerpt = tools.extract_text_from_docx(file_path)
        elif file_ext in config.IMAGE_EXTENSIONS:
            text_excerpt = tools.extract_text_from_image(file_path)
        elif file_ext in config.TEXT_EXTENSIONS:
            text_excerpt = tools.read_text_file(file_path, config.MAX_CHARS_PER_FILE)
        else:
            logging.info(f"Skipping file with unhandled extension: {file_info['name']}")
            return None
    except (OSError, ValueError) as e:
        logging.error(f"Error extracting text from {file_info['name']}: {e}")
        # Even on error, we can try to classify based on filename alone
        text_excerpt = f"Error reading file content: {e}"

    # Truncate for the LLM
    truncated_excerpt = text_excerpt[:config.MAX_CHARS_PER_FILE]

    # Get classification from LLM
    classification = llm_agent.classify_file_with_llm(
        client=client,
        model=model,
        filename=file_info["name"],
        extension=file_ext,
        text_excerpt=truncated_excerpt,
    )

    suggested_basename = classification.get("suggested_basename", f"unclassified_{Path(file_info['name']).stem}")
    
    category = classification.get("category")
    # Sanitize category for filesystem safety. Remove path separators.
    safe_category = ""
    if category:
        # Replace common path separators with underscores and strip leading/trailing whitespace
        safe_category = category.replace("/", "_").replace("\\", "_").strip()
        # Further sanitize to remove any characters that might be problematic for filenames
        # For simplicity, let's keep it to alphanumeric and underscores
        safe_category = "".join(c for c in safe_category if c.isalnum() or c == '_').strip('_')
        
    final_file_name = f"{suggested_basename}{file_ext}"

    if safe_category:
        # Construct new path with category as a subfolder
        suggested_new_path = Path(directory) / safe_category / final_file_name
    else:
        # If no category or sanitized category is empty, keep in the main directory
        suggested_new_path = Path(directory) / final_file_name

    # Assemble the plan entry
    return {
        "old_path": file_info["path"],
        "old_name": file_info["name"],
        "extension": file_ext,
        "suggested_basename": suggested_basename,
        "suggested_new_name": suggested_new_path.name, # Update this to reflect actual file name
        "suggested_new_path": str(suggested_new_path), # This is the full path
        "category": classification.get("category"),
        "confidence": classification.get("confidence"),
        "date": classification.get("date"),
        "description": classification.get("description"),
        "notes": classification.get("notes"),
    }


def build_plan_for_directory(directory: str, model: str = config.DEFAULT_MODEL) -> list[dict]:
    """
    Scans a directory, classifies each file using an LLM, and builds a plan for renaming.

    This function performs a "dry run" and does not modify any files.

    Args:
        directory: The path to the directory to organize.
        model: The OpenAI model to use for classification.

    Returns:
        A list of dictionaries, where each dictionary is a "plan entry"
        detailing the proposed changes for a single file.
    """
    plan = []
    files_to_process = tools.list_files(directory)
    if not files_to_process:
        logging.info("No files to process.")
        return []

    client = llm_agent.get_openai_client()

    # Use ThreadPoolExecutor to process files in parallel
    # Adjust max_workers as needed. OpenAI API limits might be the bottleneck,
    # but threading helps with I/O (file reading/OCR) and waiting for API responses.
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_file = {
            executor.submit(_process_file, file_info, directory, model, client): file_info 
            for file_info in files_to_process
        }
        
        for future in concurrent.futures.as_completed(future_to_file):
            file_info = future_to_file[future]
            try:
                result = future.result()
                if result:
                    plan.append(result)
            except Exception as e:
                logging.error(f"Exception processing file {file_info['name']}: {e}")

    return plan


def apply_plan(plan: list[dict]) -> list[dict]:
    """
    Executes a renaming plan.

    Args:
        plan: A list of plan entries generated by `build_plan_for_directory`.

    Returns:
        An updated list of entries, with final paths after renaming.
    """
    if not plan:
        logging.warning("Apply plan called with an empty plan.")
        return []

    logging.info("Applying organization plan...")
    updated_plan = []
    for entry in plan:
        if entry.get("category") == "error":
            logging.warning(f"Skipping rename for {entry['old_name']} due to processing error.")
            updated_entry = entry.copy()
            updated_entry["final_new_path"] = entry["old_path"]
            updated_entry["final_new_name"] = entry["old_name"]
        else:
            final_path = tools.rename_file(entry["old_path"], entry["suggested_new_path"])
            updated_entry = entry.copy()
            updated_entry["final_new_path"] = final_path
            updated_entry["final_new_name"] = Path(final_path).name
        
        updated_plan.append(updated_entry)
        
    logging.info(f"Applied plan for {len(updated_plan)} files.")
    return updated_plan


def organize_directory(directory: str, model: str = config.DEFAULT_MODEL, apply: bool = False) -> dict:
    """
    High-level function to organize a directory.

    Builds a plan, and if `apply` is True, executes it and writes metadata.

    Args:
        directory: The directory to organize.
        model: The LLM model to use.
        apply: If True, renames files and writes metadata.

    Returns:
        A summary dictionary of the operation.
    """
    summary = {
        "directory": directory,
        "applied": False,
        "num_files": 0,
        "plan": [],
        "metadata_path": None,
    }

    plan = build_plan_for_directory(directory, model)
    summary["plan"] = plan
    summary["num_files"] = len(plan)

    if apply and plan:
        applied_plan = apply_plan(plan)
        summary["plan"] = applied_plan # Update with final paths
        summary["applied"] = True
        
        metadata_path = tools.write_metadata_json(directory, applied_plan)
        summary["metadata_path"] = metadata_path

    return summary
