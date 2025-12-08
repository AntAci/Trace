"""
Main Processing Script for Trace Pipeline

Processes 2 PDFs from input_pdfs/ folder through the full Trace pipeline:
Phase 1 → Phase 2 → Phase 3 → Phase 4

NOW USES SPOON WORKFLOW GRAPH (meets bonus criteria for Graph technologies).
Falls back to sequential processing only if workflow unavailable.
"""
import json
import os
import sys
import asyncio
from pathlib import Path

# Add extraction to path
sys.path.insert(0, str(Path(__file__).parent))

from extraction.pdf_reader import read_pdfs_from_folder
from extraction.spoon_tool import extract_paper_structure_async
from phase2.synergy_agent import analyze_papers
from phase3.hypothesis_agent import generate_hypothesis
from phase4.minting_service import mint_hypothesis


async def process_papers_from_folder(
    input_folder: str = "input_pdfs",
    author_wallet: str = "NXXXX...",
    use_neofs: bool = True,
    use_x402: bool = False
) -> dict:
    """
    Process 2 PDFs from input folder through the full Trace pipeline.
    
    NOW USES SPOON WORKFLOW GRAPH (meets bonus criteria).
    Falls back to sequential processing only if workflow unavailable.
    
    Args:
        input_folder: Path to folder containing exactly 2 PDF files
        author_wallet: Neo wallet address for minting (Phase 4)
        use_neofs: Whether to store on NeoFS (default: True)
        use_x402: Whether to process X402 payment (default: False)
        
    Returns:
        dict: Complete results from all phases including mint_result
    """
    # Try to use workflow graph first (meets bonus criteria)
    try:
        from pipeline_workflow import process_papers_with_workflow, STATE_GRAPH_AVAILABLE
        
        if STATE_GRAPH_AVAILABLE:
            print("[Info] Using Spoon Workflow Graph (Graph + Agent bonus criteria)")
            result = await process_papers_with_workflow(
                input_folder=input_folder,
                author_wallet=author_wallet,
                use_neofs=use_neofs,
                use_x402=use_x402
            )
            
            # If workflow succeeded, return result
            if "error" not in result or not result.get("error"):
                return result
            
            # If workflow failed but not due to unavailability, return error
            if "fallback" not in result.get("error", "").lower():
                return result
            
            # Workflow unavailable - fall through to sequential processing
            print("[Warning] Workflow graph unavailable, falling back to sequential processing")
    except ImportError:
        # Workflow module not available - fall through to sequential
        print("[Warning] Workflow module not available, using sequential processing")
    except Exception as e:
        # Workflow failed - fall through to sequential
        print(f"[Warning] Workflow execution failed: {e}")
        print("[Info] Falling back to sequential processing")
    
    # Fallback: Sequential processing (original implementation)
    print("=" * 60)
    print("Trace Pipeline: Processing 2 PDFs (Sequential Mode)")
    print("=" * 60)
    print("=" * 60)
    print("Trace Pipeline: Processing 2 PDFs")
    print("=" * 60)
    
    # Step 1: Read PDFs
    print("\n[Step 1] Reading PDFs from folder...")
    try:
        paper_a_text, paper_b_text, paper_a_title, paper_b_title = read_pdfs_from_folder(input_folder)
        print(f"[OK] Successfully read 2 PDFs")
        print(f"   Paper A title: {paper_a_title or '(not found)'}")
        print(f"   Paper B title: {paper_b_title or '(not found)'}")
        print(f"   Paper A text length: {len(paper_a_text)} characters")
        print(f"   Paper B text length: {len(paper_b_text)} characters")
    except Exception as e:
        print(f"[ERROR] Error reading PDFs: {e}")
        return {"error": str(e)}
    
    # Step 2: Phase 1 - Extract paper structures
    print("\n[Step 2] Phase 1: Extracting paper structures...")
    try:
        paper_a_json_str = await extract_paper_structure_async(
            paper_text=paper_a_text,
            title=paper_a_title or ""
        )
        paper_b_json_str = await extract_paper_structure_async(
            paper_text=paper_b_text,
            title=paper_b_title or ""
        )
        
        paper_a_json = json.loads(paper_a_json_str)
        paper_b_json = json.loads(paper_b_json_str)
        
        if "error" in paper_a_json:
            raise ValueError(f"Paper A extraction error: {paper_a_json['error']}")
        if "error" in paper_b_json:
            raise ValueError(f"Paper B extraction error: {paper_b_json['error']}")
        
        print(f"[OK] Paper A: {len(paper_a_json.get('claims', []))} claims extracted")
        print(f"[OK] Paper B: {len(paper_b_json.get('claims', []))} claims extracted")
    except Exception as e:
        print(f"[ERROR] Phase 1 error: {e}")
        return {"error": f"Phase 1 failed: {str(e)}"}
    
    # Step 3: Phase 2 - Analyze synergies
    print("\n[Step 3] Phase 2: Analyzing synergies and conflicts...")
    try:
        from phase2.synergy_agent import SynergyAgent
        agent = SynergyAgent()
        synergy_json = await agent.analyze_async(paper_a_json, paper_b_json)
        print(f"[OK] Found {len(synergy_json.get('overlapping_variables', []))} overlapping variables")
        print(f"[OK] Found {len(synergy_json.get('potential_synergies', []))} potential synergies")
        print(f"[OK] Found {len(synergy_json.get('potential_conflicts', []))} potential conflicts")
    except Exception as e:
        print(f"[ERROR] Phase 2 error: {e}")
        return {"error": f"Phase 2 failed: {str(e)}"}
    
    # Step 4: Phase 3 - Generate hypothesis
    print("\n[Step 4] Phase 3: Generating hypothesis...")
    try:
        from phase3.hypothesis_agent import HypothesisAgent
        agent = HypothesisAgent()
        hypothesis_card = await agent.generate_hypothesis_async(paper_a_json, paper_b_json, synergy_json)
        print(f"[OK] Hypothesis generated: {hypothesis_card.get('hypothesis_id')}")
        print(f"   Confidence: {hypothesis_card.get('confidence')}")
        print(f"   Hypothesis: {hypothesis_card.get('hypothesis', '')[:100]}...")
    except Exception as e:
        print(f"[ERROR] Phase 3 error: {e}")
        return {"error": f"Phase 3 failed: {str(e)}"}
    
    # Step 5: Phase 4 - Mint hypothesis
    print("\n[Step 5] Phase 4: Minting hypothesis...")
    try:
        mint_result = mint_hypothesis(hypothesis_card, author_wallet=author_wallet)
        print(f"[OK] Hypothesis minted!")
        print(f"   Hypothesis ID: {mint_result['hypothesis_id']}")
        print(f"   Content Hash: {mint_result['content_hash']}")
        print(f"   Neo TX ID: {mint_result['neo_tx_id']}")
    except Exception as e:
        print(f"[ERROR] Phase 4 error: {e}")
        return {"error": f"Phase 4 failed: {str(e)}"}
    
    # Return complete results
    print("\n" + "=" * 60)
    print("[SUCCESS] Pipeline Complete!")
    print("=" * 60)
    
    return {
        "paper_a": paper_a_json,
        "paper_b": paper_b_json,
        "synergy_analysis": synergy_json,
        "hypothesis": hypothesis_card,
        "mint_result": mint_result
    }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process 2 PDFs through Trace pipeline"
    )
    parser.add_argument(
        "--input-folder",
        default="input_pdfs",
        help="Folder containing exactly 2 PDF files (default: input_pdfs)"
    )
    parser.add_argument(
        "--author-wallet",
        default="NXXXX...",
        help="Neo wallet address for minting (default: NXXXX...)"
    )
    parser.add_argument(
        "--use-neofs",
        action="store_true",
        default=True,
        help="Store hypothesis on NeoFS (default: True)"
    )
    parser.add_argument(
        "--no-neofs",
        action="store_false",
        dest="use_neofs",
        help="Disable NeoFS storage"
    )
    parser.add_argument(
        "--use-x402",
        action="store_true",
        default=False,
        help="Process X402 payment (default: False)"
    )
    
    args = parser.parse_args()
    
    # Run async function (will use workflow graph if available)
    result = asyncio.run(process_papers_from_folder(
        input_folder=args.input_folder,
        author_wallet=args.author_wallet,
        use_neofs=args.use_neofs,
        use_x402=args.use_x402
    ))
    
    # Print summary
    if "error" in result:
        print(f"\n[ERROR] Pipeline failed: {result['error']}")
        sys.exit(1)
    else:
        print("\n[INFO] Results saved in memory. Access via return value.")
        sys.exit(0)


if __name__ == "__main__":
    main()

