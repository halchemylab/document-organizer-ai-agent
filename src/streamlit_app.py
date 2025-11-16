"""
Streamlit UI for the AI Document Organizer.

This script creates a web-based interface for users to select a directory,
review an AI-generated organization plan, and apply the changes.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

# Important: These imports should work when running `streamlit run src/streamlit_app.py` from the root.
from config import DEFAULT_MODEL, check_api_key
from organizer import build_plan_for_directory, apply_plan
from tools import write_metadata_json

# --- Helper function for folder picker ---
def pick_folder_dialog():
    """
    Opens a native OS folder browsing dialog using Tkinter.
    Returns the selected folder path or an empty string if cancelled.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_path = filedialog.askdirectory()
    root.destroy() # Destroy the Tkinter window after selection
    return folder_path

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="AI Document Organizer",
    page_icon="🤖",
    layout="wide",
)

# --- Check for API Key ---
try:
    check_api_key()
except ValueError as e:
    st.error(f"🔴 {e}")
    st.info("Please set your OpenAI API key in a `.env` file in the project root.")
    st.code("OPENAI_API_KEY='sk-...'" ) 
    st.stop()


# --- Session State Initialization ---
if "plan" not in st.session_state:
    st.session_state.plan = None
if "directory" not in st.session_state:
    st.session_state.directory = ""


# --- UI Layout ---
st.title("🤖 AI Document Organizer")
st.markdown(
    "This app helps you clean up a folder of documents. It uses an AI model to "
    "suggest better filenames and categories, then lets you apply the changes."
)

st.sidebar.header("Configuration")
model_choice = st.sidebar.text_input(
    "OpenAI Model",
    value=DEFAULT_MODEL,
    help="The model to use for classification (e.g., 'gpt-4o-mini', 'gpt-4-turbo').",
)

st.header("1. Select a Folder")

# Create a container for the text input and button to place them side-by-side
col1, col2 = st.columns([3, 1])

with col1:
    directory = st.text_input(
        "Enter the absolute path to the folder you want to organize:",
        value=st.session_state.directory,
        placeholder="e.g., C:\\Users\\YourName\\Documents\\Scans",
        key="directory_input" # Added a key for the text_input
    )
    st.session_state.directory = directory # Update session state from text input

with col2:
    st.markdown("<br>", unsafe_allow_html=True) # Add some vertical space for alignment
    if st.button("📁 Browse for Folder"):
        selected_folder = pick_folder_dialog()
        if selected_folder:
            st.session_state.directory = selected_folder
            st.rerun() # Rerun to update the text_input with the new value

if st.button("Use Current Directory"):
    cwd = str(Path.cwd().resolve())
    st.session_state.directory = cwd
    st.rerun() # Rerun to update the text_input with the new value

st.header("2. Analyze and Review Plan")

if not st.session_state.directory:
    st.info("Please enter or select a directory path above to begin.")
elif not Path(st.session_state.directory).is_dir():
    st.error("The provided path is not a valid directory. Please check it and try again.")
else:
    if st.button("🔍 Analyze (Dry Run)", type="primary"):
        with st.spinner(f"Analyzing files in '{st.session_state.directory}'... This may take a while."):
            try:
                plan = build_plan_for_directory(st.session_state.directory, model=model_choice)
                st.session_state.plan = plan
                if not plan:
                    st.warning("No processable files found in the specified directory.")
            except Exception as e:
                st.session_state.plan = None
                st.error(f"An error occurred during analysis: {e}")

    # --- Display Plan ---
    if st.session_state.plan is not None:
        if not st.session_state.plan:
            st.info("Analysis complete. No files were found to organize.")
        else:
            st.success(f"Analysis complete! Found {len(st.session_state.plan)} files to organize.")
            st.markdown("### Proposed Organization Plan")

            # Prepare data for display in a more readable format
            display_data = [
                {
                    "Old Name": item["old_name"],
                    "Suggested New Name": item.get("suggested_new_name", "N/A"),
                    "Category": item.get("category", "N/A"),
                    "Confidence": f"{item.get('confidence', 0.0):.1%}" if item.get('confidence') is not None else "N/A",
                    "Date": item.get("date", "N/A"),
                    "Description": item.get("description", "N/A"),
                }
                for item in st.session_state.plan
            ]
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)

            st.header("3. Apply Changes")
            st.warning("⚠️ **Warning:** This action will rename files on your disk. It's recommended to have a backup.")
            
            if st.button("✅ Apply Renames"):
                with st.spinner("Applying renames and saving metadata..."):
                    try:
                        updated_plan = apply_plan(st.session_state.plan)
                        metadata_path = write_metadata_json(st.session_state.directory, updated_plan)
                        
                        st.session_state.plan = updated_plan # Update the plan with final names
                        st.balloons()
                        st.success(f"Successfully organized {len(updated_plan)} files!")
                        st.info(f"A detailed log has been saved to: `{metadata_path}`")
                        
                        # Rerun to refresh the dataframe with final names
                        st.rerun()

                    except Exception as e:
                        st.error(f"An error occurred while applying the plan: {e}")

# --- Footer ---
st.markdown("---")
st.markdown("Developed by an AI assistant.")
