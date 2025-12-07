"""
Trace Pipeline Workflow Orchestration

This module implements a Spoon StateGraph workflow that orchestrates the Trace pipeline:
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4

The workflow wraps existing functions without changing them, and the knowledge graph
stays as dict-based (not Spoon graph objects).
"""
import json
import asyncio
from typing import TypedDict, Optional, Dict, Any
from datetime import datetime, timezone

# Try to import StateGraph
try:
    from spoon_ai.graph import StateGraph, START, END
    STATE_GRAPH_AVAILABLE = True
except ImportError:
    STATE_GRAPH_AVAILABLE = False
    print("[Warning] spoon_ai.graph.StateGraph not available. Workflow will not work.")
    StateGraph = None
    START = "__start__"
    END = "__end__"

# Import pipeline functions
from extraction.pdf_reader import read_pdfs_from_folder
from extraction.spoon_tool import extract_paper_structure_async
from phase2.synergy_agent import SynergyAgent
from phase3.hypothesis_agent import HypothesisAgent
from phase4.minting_service import mint_hypothesis


# ============================================================================
# State Schema Definition
# ============================================================================

class PipelineState(TypedDict, total=False):
    """
    Complete state that flows through the workflow.
    
    All fields are optional (total=False) to allow incremental building.
    """
    # Input parameters
    input_folder: str
    author_wallet: str
    use_neofs: bool
    use_x402: bool
    
    # Phase 0 outputs
    paper_a_text: str
    paper_b_text: str
    paper_a_title: Optional[str]
    paper_b_title: Optional[str]
    
    # Phase 1 outputs
    paper_a_json: Dict[str, Any]
    paper_b_json: Dict[str, Any]
    
    # Phase 2 outputs
    synergy_json: Dict[str, Any]  # includes graph dict
    
    # Phase 3 outputs
    hypothesis_card: Dict[str, Any]
    
    # Phase 4 outputs
    mint_result: Dict[str, Any]
    
    # Error handling
    error: Optional[str]
    error_phase: Optional[str]  # "phase0", "phase1", "phase2", "phase3", "phase4"
    
    # Metadata
    pipeline_started_at: str  # ISO timestamp
    pipeline_completed_at: Optional[str]


# ============================================================================
# Node Handlers
# ============================================================================

async def read_pdfs_node(state: PipelineState) -> PipelineState:
    """
    Node 1: Read PDFs from folder (Phase 0).
    
    Wraps: read_pdfs_from_folder()
    """
    if "error" in state and state.get("error"):
        return state  # Skip if previous error
    
    try:
        paper_a_text, paper_b_text, paper_a_title, paper_b_title = \
            await asyncio.to_thread(
                read_pdfs_from_folder,
                state["input_folder"]
            )
        
        state["paper_a_text"] = paper_a_text
        state["paper_b_text"] = paper_b_text
        state["paper_a_title"] = paper_a_title
        state["paper_b_title"] = paper_b_title
        
        print(f"[Workflow] Phase 0: Read PDFs")
        print(f"   Paper A: {paper_a_title or '(no title)'} ({len(paper_a_text)} chars)")
        print(f"   Paper B: {paper_b_title or '(no title)'} ({len(paper_b_text)} chars)")
        
        return state
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        state["error"] = error_msg
        state["error_phase"] = "phase0"
        print(f"[Workflow] Phase 0 ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return state


async def extract_paper_a_node(state: PipelineState) -> PipelineState:
    """
    Node 2a: Extract Paper A structure (Phase 1, parallel).
    
    Wraps: extract_paper_structure_async()
    """
    if "error" in state and state.get("error"):
        return state  # Skip if previous error
    
    try:
        json_str = await extract_paper_structure_async(
            paper_text=state["paper_a_text"],
            title=state.get("paper_a_title", "")
        )
        paper_a_json = json.loads(json_str)
        
        if "error" in paper_a_json:
            raise ValueError(f"Extraction error: {paper_a_json['error']}")
        
        state["paper_a_json"] = paper_a_json
        
        print(f"[Workflow] Phase 1a: Extracted Paper A ({len(paper_a_json.get('claims', []))} claims)")
        
        return state
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        state["error"] = error_msg
        state["error_phase"] = "phase1"
        print(f"[Workflow] Phase 1a ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return state


async def extract_paper_b_node(state: PipelineState) -> PipelineState:
    """
    Node 2b: Extract Paper B structure (Phase 1, parallel).
    
    Wraps: extract_paper_structure_async()
    """
    if "error" in state and state.get("error"):
        return state  # Skip if previous error
    
    try:
        json_str = await extract_paper_structure_async(
            paper_text=state["paper_b_text"],
            title=state.get("paper_b_title", "")
        )
        paper_b_json = json.loads(json_str)
        
        if "error" in paper_b_json:
            raise ValueError(f"Extraction error: {paper_b_json['error']}")
        
        state["paper_b_json"] = paper_b_json
        
        print(f"[Workflow] Phase 1b: Extracted Paper B ({len(paper_b_json.get('claims', []))} claims)")
        
        return state
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        state["error"] = error_msg
        state["error_phase"] = "phase1"
        print(f"[Workflow] Phase 1b ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return state


async def analyze_synergy_node(state: PipelineState) -> PipelineState:
    """
    Node 3: Analyze synergies and conflicts (Phase 2).
    
    Wraps: SynergyAgent.analyze_async()
    """
    if "error" in state and state.get("error"):
        return state  # Skip if previous error
    
    try:
        agent = SynergyAgent()
        synergy_json = await agent.analyze_async(
            state["paper_a_json"],
            state["paper_b_json"]
        )
        
        state["synergy_json"] = synergy_json
        
        print(f"[Workflow] Phase 2: Analyzed synergies")
        print(f"   Overlapping variables: {len(synergy_json.get('overlapping_variables', []))}")
        print(f"   Potential synergies: {len(synergy_json.get('potential_synergies', []))}")
        print(f"   Potential conflicts: {len(synergy_json.get('potential_conflicts', []))}")
        
        return state
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        state["error"] = error_msg
        state["error_phase"] = "phase2"
        print(f"[Workflow] Phase 2 ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return state


async def generate_hypothesis_node(state: PipelineState) -> PipelineState:
    """
    Node 4: Generate hypothesis (Phase 3).
    
    Wraps: HypothesisAgent.generate_hypothesis_async()
    """
    if "error" in state and state.get("error"):
        return state  # Skip if previous error
    
    try:
        agent = HypothesisAgent()
        hypothesis_card = await agent.generate_hypothesis_async(
            state["paper_a_json"],
            state["paper_b_json"],
            state["synergy_json"]
        )
        
        state["hypothesis_card"] = hypothesis_card
        
        print(f"[Workflow] Phase 3: Generated hypothesis")
        print(f"   Hypothesis ID: {hypothesis_card.get('hypothesis_id')}")
        print(f"   Confidence: {hypothesis_card.get('confidence')}")
        
        return state
    except Exception as e:
        state["error"] = str(e)
        state["error_phase"] = "phase3"
        print(f"[Workflow] Phase 3 ERROR: {e}")
        return state


async def mint_hypothesis_node(state: PipelineState) -> PipelineState:
    """
    Node 5: Mint hypothesis (Phase 4).
    
    Wraps: mint_hypothesis()
    """
    if "error" in state and state.get("error"):
        return state  # Skip if previous error
    
    try:
        mint_result = await asyncio.to_thread(
            mint_hypothesis,
            card=state["hypothesis_card"],
            author_wallet=state["author_wallet"],
            use_neofs=state.get("use_neofs", True),
            use_x402=state.get("use_x402", False)
        )
        
        state["mint_result"] = mint_result
        state["pipeline_completed_at"] = datetime.now(timezone.utc).isoformat()
        
        print(f"[Workflow] Phase 4: Minted hypothesis")
        print(f"   Hypothesis ID: {mint_result.get('hypothesis_id')}")
        print(f"   Content Hash: {mint_result.get('content_hash')}")
        print(f"   Neo TX ID: {mint_result.get('neo_tx_id')}")
        
        return state
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        state["error"] = error_msg
        state["error_phase"] = "phase4"
        print(f"[Workflow] Phase 4 ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return state


# ============================================================================
# Workflow Graph Builder
# ============================================================================

def build_pipeline_workflow() -> Any:
    """
    Build the Trace pipeline workflow graph.
    
    Returns:
        Compiled workflow graph (CompiledGraph) or None if StateGraph unavailable
    """
    if not STATE_GRAPH_AVAILABLE:
        print("[Warning] StateGraph not available. Cannot build workflow.")
        return None
    
    # Create graph with state schema
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("read_pdfs", read_pdfs_node)
    workflow.add_node("extract_paper_a", extract_paper_a_node)
    workflow.add_node("extract_paper_b", extract_paper_b_node)
    workflow.add_node("analyze_synergy", analyze_synergy_node)
    workflow.add_node("generate_hypothesis", generate_hypothesis_node)
    workflow.add_node("mint_hypothesis", mint_hypothesis_node)
    
    # Set entry point
    workflow.set_entry_point("read_pdfs")
    
    # Add edges: sequential flow
    # Phase 0 → Phase 1 (parallel - both extractions run simultaneously)
    workflow.add_edge("read_pdfs", "extract_paper_a")
    workflow.add_edge("read_pdfs", "extract_paper_b")
    
    # Add parallel group for Phase 1 (both extractions run simultaneously)
    workflow.add_parallel_group("extract_papers_parallel", ["extract_paper_a", "extract_paper_b"])
    
    # After both extractions complete, continue to Phase 2
    # Connect only one node - parallel group ensures both complete before continuing
    workflow.add_edge("extract_paper_a", "analyze_synergy")
    workflow.add_edge("analyze_synergy", "generate_hypothesis")
    workflow.add_edge("generate_hypothesis", "mint_hypothesis")
    workflow.add_edge("mint_hypothesis", END)
    
    # Compile graph
    try:
        compiled = workflow.compile()
        print("[Workflow] Pipeline workflow graph compiled successfully")
        return compiled
    except Exception as e:
        print(f"[Error] Failed to compile workflow graph: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# Entry Point
# ============================================================================

async def process_papers_with_workflow(
    input_folder: str = "input_pdfs",
    author_wallet: str = "NXXXX...",
    use_neofs: bool = True,
    use_x402: bool = False
) -> Dict[str, Any]:
    """
    Process 2 PDFs through Trace pipeline using Spoon workflow graph.
    
    Args:
        input_folder: Path to folder containing exactly 2 PDF files
        author_wallet: Neo wallet address for minting (Phase 4)
        use_neofs: Whether to store on NeoFS (default: True)
        use_x402: Whether to process X402 payment (default: False)
        
    Returns:
        dict: Complete results from all phases including mint_result,
              or error dict if workflow unavailable or failed
    """
    if not STATE_GRAPH_AVAILABLE:
        return {
            "error": "StateGraph not available. Install spoon-ai-sdk>=0.3.4",
            "fallback": "Use process_papers_from_folder() instead"
        }
    
    # Build workflow graph
    workflow = build_pipeline_workflow()
    if workflow is None:
        return {
            "error": "Failed to build workflow graph",
            "fallback": "Use process_papers_from_folder() instead"
        }
    
    # Initialize state
    initial_state: PipelineState = {
        "input_folder": input_folder,
        "author_wallet": author_wallet,
        "use_neofs": use_neofs,
        "use_x402": use_x402,
        "pipeline_started_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Run workflow
    print("=" * 70)
    print("TRACE PIPELINE - WORKFLOW ORCHESTRATION")
    print("=" * 70)
    print(f"Input folder: {input_folder}")
    print(f"Author wallet: {author_wallet}")
    print(f"NeoFS: {use_neofs}, X402: {use_x402}")
    print("=" * 70)
    
    try:
        print("[DEBUG] Invoking workflow...")
        print(f"[DEBUG] Initial state keys: {list(initial_state.keys())}")
        final_state = await workflow.invoke(initial_state)
        print(f"[DEBUG] Workflow completed. State keys: {list(final_state.keys())}")
        
        # Debug: Print actual values
        print(f"[DEBUG] paper_a_json type: {type(final_state.get('paper_a_json'))}")
        print(f"[DEBUG] paper_b_json type: {type(final_state.get('paper_b_json'))}")
        print(f"[DEBUG] synergy_json type: {type(final_state.get('synergy_json'))}")
        print(f"[DEBUG] hypothesis_card type: {type(final_state.get('hypothesis_card'))}")
        print(f"[DEBUG] mint_result type: {type(final_state.get('mint_result'))}")
        
        # Debug: Print state keys
        if "error" in final_state:
            error_val = final_state.get("error")
            print(f"[DEBUG] Error in state: {error_val} (type: {type(error_val)})")
            print(f"[DEBUG] Error phase: {final_state.get('error_phase')}")
        
        # Check for errors (only if error value is truthy, not just if key exists)
        error_val = final_state.get("error")
        if error_val:  # Only treat as error if value is truthy (not None, not empty string)
            error_phase = final_state.get("error_phase", "unknown")
            print(f"\n[ERROR] Pipeline failed at {error_phase}")
            print(f"Error: {error_val}")
            return {
                "error": error_val,
                "error_phase": error_phase,
                "partial_results": {
                    k: v for k, v in final_state.items()
                    if k not in ["error", "error_phase"]
                }
            }
        
        # Success - return complete results
        print("\n" + "=" * 70)
        print("[SUCCESS] Pipeline Complete!")
        print("=" * 70)
        
        return {
            "paper_a": final_state.get("paper_a_json"),
            "paper_b": final_state.get("paper_b_json"),
            "synergy_analysis": final_state.get("synergy_json"),
            "hypothesis": final_state.get("hypothesis_card"),
            "mint_result": final_state.get("mint_result"),
            "pipeline_started_at": final_state.get("pipeline_started_at"),
            "pipeline_completed_at": final_state.get("pipeline_completed_at")
        }
        
    except Exception as e:
        print(f"\n[ERROR] Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }

