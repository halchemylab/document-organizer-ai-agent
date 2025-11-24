import pytest
from unittest.mock import MagicMock
from src import organizer, config

@pytest.fixture
def mock_dependencies(mocker):
    # Mock tools functions to avoid disk I/O and external deps
    mocker.patch("src.tools.list_files", return_value=[
        {"path": "/tmp/doc.txt", "name": "doc.txt", "ext": ".txt"},
        {"path": "/tmp/image.png", "name": "image.png", "ext": ".png"}
    ])
    mocker.patch("src.tools.read_text_file", return_value="sample text content")
    mocker.patch("src.tools.extract_text_from_image", return_value="ocr text")
    
    # Mock LLM agent
    mock_client = MagicMock()
    mocker.patch("src.llm_agent.get_openai_client", return_value=mock_client)
    
    mocker.patch("src.llm_agent.classify_file_with_llm", side_effect=[
        {
            "suggested_basename": "renamed_doc",
            "category": "document",
            "confidence": 0.9,
            "description": "A text doc"
        },
        {
            "suggested_basename": "renamed_image",
            "category": "image",
            "confidence": 0.8,
            "description": "An image"
        }
    ])

def test_build_plan_for_directory(mock_dependencies):
    plan = organizer.build_plan_for_directory("/tmp")
    
    assert len(plan) == 2
    
    # Check first item (text file)
    item1 = plan[0]
    assert item1["old_name"] == "doc.txt"
    assert item1["suggested_new_name"] == "renamed_doc.txt"
    assert item1["category"] == "document"
    
    # Check second item (image)
    item2 = plan[1]
    assert item2["old_name"] == "image.png"
    assert item2["suggested_new_name"] == "renamed_image.png"
    assert item2["category"] == "image"

def test_apply_plan(mocker):
    # Mock rename_file
    mocker.patch("src.tools.rename_file", side_effect=lambda old, new: new)
    
    plan = [
        {
            "old_path": "/tmp/old.txt",
            "old_name": "old.txt",
            "suggested_new_path": "/tmp/new.txt",
            "category": "document"
        },
        {
            "old_path": "/tmp/err.txt",
            "old_name": "err.txt",
            "suggested_new_path": "/tmp/err_new.txt",
            "category": "error" # Should be skipped
        }
    ]
    
    updated_plan = organizer.apply_plan(plan)
    
    assert len(updated_plan) == 2
    # First one renamed
    assert updated_plan[0]["final_new_path"] == "/tmp/new.txt"
    
    # Second one skipped (error category)
    assert updated_plan[1]["final_new_path"] == "/tmp/err.txt"
