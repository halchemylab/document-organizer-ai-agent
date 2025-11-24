import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from src import tools

def test_list_files(tmp_path):
    # Setup
    f1 = tmp_path / "test1.txt"
    f1.write_text("content")
    f2 = tmp_path / "image.png"
    f2.touch()
    d1 = tmp_path / "subdir"
    d1.mkdir()
    
    # Execute
    files = tools.list_files(str(tmp_path))
    
    # Verify
    assert len(files) == 2
    names = [f["name"] for f in files]
    assert "test1.txt" in names
    assert "image.png" in names

def test_read_text_file(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("Hello world")
    
    content = tools.read_text_file(str(f))
    assert content == "Hello world"

def test_rename_file_simple(tmp_path):
    old_file = tmp_path / "old.txt"
    old_file.write_text("data")
    new_path = tmp_path / "new.txt"
    
    final_path = tools.rename_file(str(old_file), str(new_path))
    
    assert Path(final_path).name == "new.txt"
    assert Path(final_path).exists()
    assert not old_file.exists()

def test_rename_file_collision(tmp_path):
    # Setup: Create existing files to force collision
    old_file = tmp_path / "file.txt"
    old_file.write_text("new content")
    
    target_file = tmp_path / "target.txt"
    target_file.write_text("existing content")
    
    # Execute
    final_path = tools.rename_file(str(old_file), str(target_file))
    
    # Verify it created target_1.txt
    assert Path(final_path).name == "target_1.txt"
    assert Path(final_path).exists()
    assert target_file.exists() # Original should still be there

def test_extract_text_from_docx(mocker):
    # Mock docx.Document
    mock_doc = MagicMock()
    p1 = MagicMock()
    p1.text = "Hello"
    p2 = MagicMock()
    p2.text = "World"
    mock_doc.paragraphs = [p1, p2]
    
    mocker.patch("docx.Document", return_value=mock_doc)
    
    text = tools.extract_text_from_docx("dummy.docx")
    assert "Hello\nWorld\n" == text
