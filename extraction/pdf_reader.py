"""
PDF Reading Module for Trace Phase 1

Extracts text from PDF files for paper structure extraction.
"""
import os
from typing import Tuple, Optional

try:
    from PyPDF2 import PdfReader
except ImportError:
    raise ImportError("PyPDF2>=3.0 is required. Install with: pip install PyPDF2>=3.0")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract title and abstract from a PDF file.
    
    Only extracts the abstract section, not the full paper text.
    This reduces token usage and focuses on key information.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError(f"File is not a PDF: {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
        
        if len(reader.pages) == 0:
            raise ValueError(f"PDF is empty: {pdf_path}")
        
        # Extract text from first 2 pages -- Title and Abstract 
        text_parts = []
        for i, page in enumerate(reader.pages[:2]):  
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        if not text_parts:
            raise ValueError(f"No text could be extracted from PDF: {pdf_path}")
        
        full_text = "\n\n".join(text_parts)
        
        # Extract title and abstract
        title = extract_title_from_pdf(pdf_path) or ""
        abstract_text = _extract_abstract_section(full_text)
        
        # Combine title and abstract
        if title:
            combined = f"{title}\n\n{abstract_text}"
        else:
            combined = abstract_text
        
        return combined.strip()
        
    except Exception as e:
        raise ValueError(f"Error reading PDF {pdf_path}: {str(e)}")


def _extract_abstract_section(text: str) -> str:
    """
    Extract abstract section from paper text.
    
    Looks for "Abstract" or "ABSTRACT" keyword and extracts text until
    keywords like "Keywords", "Introduction", "1. Introduction", etc.
    """
    text_lower = text.lower()
    
    # Find abstract start
    abstract_markers = ["abstract", "summary"]
    abstract_start = -1
    
    for marker in abstract_markers:
        pos = text_lower.find(marker)
        if pos != -1:
            # Move past the word "abstract" and any following punctuation/whitespace
            abstract_start = pos + len(marker)
            # Skip whitespace, colons, newlines
            while abstract_start < len(text) and text[abstract_start] in " \n\r\t:":
                abstract_start += 1
            break
    
    if abstract_start == -1:
        # No abstract found, return first 3000 characters
        return text[:3000] if len(text) > 3000 else text
    
    # Find abstract end (look for common section markers)
    end_markers = [
        "\nkeywords",
        "\nkey words",
        "\n1. introduction",
        "\nintroduction",
        "\n1 introduction",
        "\n2. ",
        "\n2 ",
        "\nbackground",
        "\n1. background"
    ]
    
    abstract_end = len(text)
    text_after_abstract = text_lower[abstract_start:]
    
    for marker in end_markers:
        pos = text_after_abstract.find(marker)
        if pos != -1 and pos < abstract_end:
            abstract_end = abstract_start + pos
            break
    
    # Extract abstract
    abstract = text[abstract_start:abstract_end].strip()
    
    # Limit to 5000 characters max 
    if len(abstract) > 5000:
        abstract = abstract[:5000]
    
    return abstract


def extract_title_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Try to extract title from PDF metadata or first page.
    """
    try:
        reader = PdfReader(pdf_path)
        
        # Try metadata first
        if reader.metadata and reader.metadata.title:
            title = reader.metadata.title.strip()
            if title:
                return title
        
        # Try first line of first page
        if len(reader.pages) > 0:
            first_page_text = reader.pages[0].extract_text()
            if first_page_text:
                first_line = first_page_text.split('\n')[0].strip()
                # Heuristic: if first line is short and looks like a title
                if len(first_line) < 200 and len(first_line) > 10:
                    return first_line
        
        return None
        
    except Exception:
        return None


def read_pdfs_from_folder(folder_path: str = "input_pdfs") -> Tuple[str, str, Optional[str], Optional[str]]:
    """
    Read exactly 2 PDF files from the specified folder.
    
    Extracts only title and abstract from each PDF to reduce token usage.
    """
    if not os.path.exists(folder_path):
        raise ValueError(f"Input folder does not exist: {folder_path}")
    
    if not os.path.isdir(folder_path):
        raise ValueError(f"Path is not a directory: {folder_path}")
    
    # Find all PDF files in folder
    pdf_files = [f for f in os.listdir(folder_path) 
                 if f.lower().endswith('.pdf')]
    
    if len(pdf_files) == 0:
        raise ValueError(f"No PDF files found in {folder_path}")
    
    if len(pdf_files) < 2:
        raise ValueError(f"Found only {len(pdf_files)} PDF file(s) in {folder_path}. Need exactly 2 PDFs.")
    
    if len(pdf_files) > 2:
        raise ValueError(f"Found {len(pdf_files)} PDF files in {folder_path}. Need exactly 2 PDFs. Found: {', '.join(pdf_files)}")
    
    # Sort to ensure consistent ordering
    pdf_files.sort()
    
    # Read both PDFs
    pdf_a_path = os.path.join(folder_path, pdf_files[0])
    pdf_b_path = os.path.join(folder_path, pdf_files[1])
    
    try:
        # Extract title and abstract 
        paper_a_text = extract_text_from_pdf(pdf_a_path)
        paper_b_text = extract_text_from_pdf(pdf_b_path)
        
        # Also extract titles separately for reference
        paper_a_title = extract_title_from_pdf(pdf_a_path)
        paper_b_title = extract_title_from_pdf(pdf_b_path)
        
        return paper_a_text, paper_b_text, paper_a_title, paper_b_title
        
    except Exception as e:
        raise ValueError(f"Error reading PDFs: {str(e)}")

