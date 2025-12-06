"""
Phase 1: SpoonOS Tool for Paper Structure Extraction.

This is the ONLY tool in Phase 1. It converts paper text into structured JSON.
"""
import json
import sys
from pathlib import Path

# Add extraction directory to path for imports
extraction_dir = Path(__file__).parent
if str(extraction_dir) not in sys.path:
    sys.path.insert(0, str(extraction_dir))

from extract_paper import extract_paper

try:
    from spoon_ai import Tool
    SPOON_AVAILABLE = True
except ImportError:
    SPOON_AVAILABLE = False
    print("[Warning] spoon-ai-sdk not installed. Tool registration disabled.")
    print("Install with: pip install spoon-ai-sdk")


async def extract_paper_structure_async(paper_text: str, title: str = "") -> str:
    """
    Async SpoonOS Tool: Extract structured scientific information from paper text.
    
    This tool takes paper text (typically abstract) and returns structured JSON
    with claims, methods, evidence, limitations, and variables.
    
    Args:
        paper_text: The paper text (string) - typically the abstract
        title: Optional paper title (string) for better extraction quality
    
    Returns:
        str: JSON string with structured extraction containing:
            - claims (all claims)
            - methods
            - evidence (1-2 items)
            - explicit_limitations
            - implicit_limitations
            - variables
    """
    # Input validation
    if not paper_text or not isinstance(paper_text, str):
        return json.dumps({"error": "paper_text must be a non-empty string"}, indent=2)
    
    if len(paper_text.strip()) == 0:
        return json.dumps({"error": "paper_text cannot be empty"}, indent=2)
    
    if title and not isinstance(title, str):
        return json.dumps({"error": "title must be a string"}, indent=2)
    
    try:
        # Call extraction function (synchronous, but wrapped in async)
        result = extract_paper(paper_text.strip(), title.strip() if title else "")
        
        # Validate output structure
        required_fields = ["claims", "methods", "evidence", "explicit_limitations", "implicit_limitations", "variables"]
        for field in required_fields:
            if field not in result:
                result[field] = []
        
        # Ensure evidence is limited to 1-2 items
        if isinstance(result.get("evidence"), list):
            result["evidence"] = result["evidence"][:2]
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def create_extraction_tool():
    """
    Create the SpoonOS tool for paper structure extraction.
    """
    if not SPOON_AVAILABLE:
        raise ImportError("spoon-ai-sdk is required. Install with: pip install spoon-ai-sdk")
    
    tool = Tool(
        name="extract_paper_structure",
        description="Extract structured scientific information from a paper's text (typically abstract). Returns JSON with claims (all), methods, evidence (1-2), explicit/implicit limitations, and variables. Uses Groq LLM internally.",
        func=extract_paper_structure_async,
        parameters={
            "paper_text": {
                "type": "string",
                "description": "The paper text to extract from (typically the abstract)",
                "required": True
            },
            "title": {
                "type": "string",
                "description": "Optional paper title for better extraction quality",
                "required": False,
                "default": ""
            }
        }
    )
    
    return tool


# Export the tool creation function
__all__ = ["create_extraction_tool", "extract_paper_structure_async"]


if __name__ == "__main__":
    # Test tool creation (no agent needed in Phase 1)
    if SPOON_AVAILABLE:
        try:
            tool = create_extraction_tool()
            print("✅ Phase 1 SpoonOS tool created successfully!")
            print(f"Tool name: {tool.name}")
            print(f"Tool description: {tool.description}")
            print("\nTool is ready for use. No agents needed in Phase 1.")
        except Exception as e:
            print(f"Error creating tool: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("SpoonOS SDK not available. Install with: pip install spoon-ai-sdk")
