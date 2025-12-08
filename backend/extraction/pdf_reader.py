"""
PDF Reading Module for Trace Phase 1

Strategy: First-5-Last-1 Hybrid for Universal Coverage

Extracts text from PDF files for paper structure extraction.
"""
import os
import glob
from typing import Tuple, Optional

try:
    from PyPDF2 import PdfReader
except ImportError:
    raise ImportError("PyPDF2>=3.0 is required. Install with: pip install PyPDF2>=3.0")


def extract_text_smart(pdf_path: str, max_chars: int = 12000) -> Tuple[str, Optional[str]]:
    """
    Extracts text using a 'Methodology-First' strategy.
    
    STRATEGY:
    1. Page 1: Abstract & Intro (The Problem).
    2. SKIP Page 2: Usually 'Related Work' (Wastes tokens).
    3. Page 3-5: System Design & Methodology (The specific Mechanisms like ROCL).
    4. Last Page: Conclusion.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        
        if total_pages == 0:
            raise ValueError(f"PDF is empty: {pdf_path}")
        full_text = []
        
        # 1. Read Abstract/Intro (Page 1)
        if total_pages > 0:
            print(f"[PDF Reader] Reading Page 1 (Intro)...")
            full_text.append(reader.pages[0].extract_text())

        # 2. SKIP Page 2 (Related Work), JUMP to Methodology (Page 3, 4, 5)
        # This ensures we catch 'ROCL' on Page 4 before hitting the 12k limit.
        start_page = 2  # 0-indexed, so this is Page 3
        end_page = min(5, total_pages)
        
        if end_page > start_page:
            print(f"[PDF Reader] Reading Pages {start_page+1}-{end_page} (Methodology)...")
            for i in range(start_page, end_page):
                text = reader.pages[i].extract_text()
                if text: full_text.append(text)

        # 3. Conclusion (Last Page)
        if total_pages > 5:
            print(f"[PDF Reader] Appending last page (Conclusion)...")
            last_page_text = reader.pages[-1].extract_text()
            if last_page_text:
                full_text.append("\n--- [CONCLUSION] ---\n")
                full_text.append(last_page_text)
        
        combined_text = "\n".join(full_text)
        
        # 4. Clean and Truncate
        combined_text = " ".join(combined_text.split()) # Remove excess whitespace
        
        if len(combined_text) > max_chars:
            print(f"[PDF Reader] Truncating text from {len(combined_text)} to {max_chars} chars.")
            combined_text = combined_text[:max_chars] + "... [TRUNCATED]"
            
        # Extract title
        title = None
        if reader.metadata and reader.metadata.title:
            title = reader.metadata.title.strip()
        if not title:
            title = os.path.basename(pdf_path)
            
        return combined_text, title
    except Exception as e:
        raise ValueError(f"Error reading PDF {pdf_path}: {str(e)}")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file (backward compatibility wrapper).
    
    Uses the new extract_text_smart() strategy internally.
    Returns only the text portion (without title).
    """
    text, _ = extract_text_smart(pdf_path)
    return text


def extract_title_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Try to extract title from PDF (backward compatibility wrapper).
    
    Uses the new extract_text_smart() strategy internally.
    Returns only the title portion.
    """
    try:
        _, title = extract_text_smart(pdf_path)
        return title
    except Exception:
        return None


def read_pdfs_from_folder(folder_path: str = "input_pdfs") -> Tuple[str, str, Optional[str], Optional[str]]:
    """
    Read exactly 2 PDF files from the specified folder.
    
    Uses the new First-5-Last-1 strategy for maximum information density.
    """
    if not os.path.exists(folder_path):
        raise ValueError(f"Input folder does not exist: {folder_path}")
    
    # Use glob to find PDFs
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    pdf_files.sort()
    
    if len(pdf_files) != 2:
        raise ValueError(f"Expected exactly 2 PDF files in {folder_path}. Found {len(pdf_files)}.")
    
    paper_a_text, paper_a_title = extract_text_smart(pdf_files[0])
    paper_b_text, paper_b_title = extract_text_smart(pdf_files[1])
    
    return paper_a_text, paper_b_text, paper_a_title, paper_b_title

