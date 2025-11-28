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

def test_extract_text_from_pdf_success(mocker, tmp_path):
    # Create a dummy PDF file so open() doesn't fail
    pdf_path = tmp_path / "test.pdf"
    pdf_path.touch()

    # Mock PyPDF2.PdfReader
    mock_reader = MagicMock()
    mock_reader.is_encrypted = False
    page1 = MagicMock()
    page1.extract_text.return_value = "Page 1 content"
    page2 = MagicMock()
    page2.extract_text.return_value = "Page 2 content"
    mock_reader.pages = [page1, page2]
    
    # Patch the PyPDF2 module imported in src.tools
    mock_pypdf2 = mocker.patch("src.tools.PyPDF2")
    mock_pypdf2.PdfReader.return_value = mock_reader
    
    text = tools.extract_text_from_pdf(str(pdf_path))
    assert "Page 1 content" in text
    assert "Page 2 content" in text

def test_pdf_file_not_found(caplog):
    tools.extract_text_from_pdf("nonexistent_file.pdf")
    assert "Failed to read or parse PDF" in caplog.text

def test_extract_text_from_pdf_encrypted(mocker, tmp_path):
    pdf_path = tmp_path / "encrypted.pdf"
    pdf_path.touch()

    mock_reader = MagicMock()
    mock_reader.is_encrypted = True
    
    # Patch the PyPDF2 module imported in src.tools
    mock_pypdf2 = mocker.patch("src.tools.PyPDF2")
    mock_pypdf2.PdfReader.return_value = mock_reader
    
    text = tools.extract_text_from_pdf(str(pdf_path))
    assert text == ""

def test_extract_text_from_image_success(mocker, tmp_path):
    img_path = tmp_path / "test.png"
    img_path.touch()
    
    # Mock Image.open (context manager)
    mock_img = MagicMock()
    mock_open = mocker.patch("src.tools.Image.open", return_value=mock_img)
    mock_img.__enter__.return_value = mock_img
    
    # Mock pytesseract
    mocker.patch("src.tools.pytesseract.image_to_string", return_value="OCR Text")
    
    text = tools.extract_text_from_image(str(img_path))
    assert text == "OCR Text"

def test_extract_text_from_image_no_tesseract(mocker, tmp_path):
    img_path = tmp_path / "test.png"
    img_path.touch()
    
    mock_img = MagicMock()
    mock_open = mocker.patch("src.tools.Image.open", return_value=mock_img)
    mock_img.__enter__.return_value = mock_img

    # Mock pytesseract raising TesseractNotFoundError
    from pytesseract import TesseractNotFoundError
    mocker.patch("src.tools.pytesseract.image_to_string", side_effect=TesseractNotFoundError)
    
    with pytest.raises(TesseractNotFoundError):
        tools.extract_text_from_image(str(img_path))