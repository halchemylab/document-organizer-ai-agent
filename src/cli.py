"""
Command-Line Interface for the AI Document Organizer.

Allows running the organization process from the terminal without the Streamlit UI.
"""
import argparse
import logging
from . import organizer, config

def main():
    """Main function for the CLI."""
    parser = argparse.ArgumentParser(description="AI-Powered Document Organizer CLI")
    parser.add_argument(
        "--directory",
        type=str,
        required=True,
        help="The path to the directory you want to organize.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=config.DEFAULT_MODEL,
        help=f"The OpenAI model to use for classification. Defaults to '{config.DEFAULT_MODEL}'.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the renaming plan. If not set, runs in dry-run mode.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.apply:
            print(f"Organizing directory '{args.directory}' and applying changes...")
        else:
            print(f"Analyzing directory '{args.directory}' (Dry Run)...")

        result = organizer.organize_directory(
            directory=args.directory,
            model=args.model,
            apply=args.apply,
        )

        print("\n--- Organization Plan ---")
        if not result["plan"]:
            print("No files found or processed.")
        else:
            for item in result["plan"]:
                print(f"  '{item['old_name']}' -> '{item.get('suggested_new_name', 'N/A')}' (Category: {item.get('category', 'N/A')})")

        print("\n--- Summary ---")
        print(f"Processed {result['num_files']} files.")
        if result["applied"]:
            print("Status: Plan APPLIED successfully.")
            print(f"Metadata saved to: {result['metadata_path']}")
        else:
            print("Status: Dry run complete. No files were changed.")
            print("To apply these changes, run with the --apply flag.")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=args.verbose)
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
