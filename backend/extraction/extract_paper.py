"""
Phase 1: Extract structured scientific information from a single paper.

This module provides the core extraction function used by the SpoonOS tool.
It converts paper text into structured JSON with claims, methods, evidence, limitations, and variables.

Input: Paper text (string) - usually the abstract
Output: Structured JSON dictionary
"""
import json
from extract_groq import extract_structure


def extract_paper(paper_text, title=""):
    """
    Extract structured scientific information from a paper's text.
    
    This is the main Phase 1 function. It converts paper text into structured JSON
    that captures essential scientific content for reasoning.
    """
    if not paper_text or len(paper_text.strip()) == 0:
        raise ValueError("Paper text cannot be empty")
    
    # Extract structured information using Groq
    structured = extract_structure(paper_text, title)
    
    # Ensure evidence is limited to 1-2 items
    if "evidence" in structured and isinstance(structured["evidence"], list):
        structured["evidence"] = structured["evidence"][:2]
    
    return structured


def extract_paper_from_json(paper_data):
    """
    Extract from a JSON object containing paper data.
    """
    text = paper_data.get("text", "") or paper_data.get("abstract", "")
    title = paper_data.get("title", "")
    
    if not text:
        raise ValueError("No text or abstract found in paper data")
    
    return extract_paper(text, title)


# SpoonOS Tool interface
def tool_extract_paper(paper_text, title=""):
    """
    SpoonOS Tool: Extract structured scientific information from paper text.
    
    This is the tool interface that the agent can call.
    """
    try:
        result = extract_paper(paper_text, title)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_paper.py <paper_text> [title]")
        print("\nExample:")
        print('  python extract_paper.py "This paper presents a novel approach..." "Paper Title"')
        sys.exit(1)
    
    paper_text = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else ""
    
    try:
        result = extract_paper(paper_text, title)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

