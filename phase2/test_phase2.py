"""
Test Phase 2: Synergy and Conflict Analysis

Tests the SynergyAgent with sample Phase 1 outputs.
"""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase2.synergy_agent import SynergyAgent, analyze_papers


def test_basic_analysis():
    """Test basic synergy and conflict analysis."""
    print("=" * 60)
    print("TEST 1: Basic Analysis")
    print("=" * 60)
    
    paper_a = {
        "claims": [
            "High temperature accelerates battery degradation",
            "Non-linear capacity fade occurs above 45°C"
        ],
        "methods": ["Accelerated aging tests at various temperatures"],
        "evidence": [
            "50% capacity loss at 60°C after 100 cycles",
            "Linear degradation below 45°C, exponential above"
        ],
        "explicit_limitations": ["Limited to NMC chemistry batteries"],
        "implicit_limitations": ["May not apply to other chemistries"],
        "variables": ["temperature", "capacity", "cycles", "degradation_rate"]
    }
    
    paper_b = {
        "claims": [
            "State of health can be predicted using temperature and voltage",
            "Linear aging model works well for most operating conditions"
        ],
        "methods": ["Machine learning regression on historical data"],
        "evidence": [
            "95% accuracy on test dataset",
            "Model assumes linear degradation"
        ],
        "explicit_limitations": ["Requires large training dataset"],
        "implicit_limitations": ["May not capture non-linear behavior"],
        "variables": ["temperature", "voltage", "state_of_health", "aging_model"]
    }
    
    try:
        result = analyze_papers(paper_a, paper_b)
        
        # Validate structure
        required_fields = ["overlapping_variables", "potential_synergies", 
                          "potential_conflicts", "graph"]
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"[FAIL] Missing fields: {missing_fields}")
            return False
        
        # Validate graph structure
        graph = result.get("graph", {})
        if "nodes" not in graph or "edges" not in graph:
            print("[FAIL] Graph missing nodes or edges")
            return False
        
        print("[PASS] Analysis successful!")
        print(f"   Overlapping variables: {len(result.get('overlapping_variables', []))} items")
        print(f"   Potential synergies: {len(result.get('potential_synergies', []))} items")
        print(f"   Potential conflicts: {len(result.get('potential_conflicts', []))} items")
        print(f"   Graph nodes: {len(graph.get('nodes', []))} items")
        print(f"   Graph edges: {len(graph.get('edges', []))} items")
        
        print("\nSample output:")
        print(json.dumps(result, indent=2)[:1000] + "...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_input_validation():
    """Test input validation."""
    print("\n" + "=" * 60)
    print("TEST 2: Input Validation")
    print("=" * 60)
    
    agent = SynergyAgent()
    
    # Test missing fields
    invalid_paper = {
        "claims": ["Test claim"]
        # Missing other required fields
    }
    
    valid_paper = {
        "claims": ["Test"],
        "methods": ["Test method"],
        "evidence": [],
        "explicit_limitations": [],
        "implicit_limitations": [],
        "variables": []
    }
    
    try:
        agent.analyze(invalid_paper, valid_paper)
        print("[FAIL] Should have raised ValueError for invalid input")
        return False
    except ValueError:
        print("[PASS] Correctly rejected invalid input")
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False
    
    return True


def test_graph_structure():
    """Test graph building."""
    print("\n" + "=" * 60)
    print("TEST 3: Graph Structure")
    print("=" * 60)
    
    paper_a = {
        "claims": ["Claim A1", "Claim A2"],
        "methods": ["Method A"],
        "evidence": ["Evidence A"],
        "explicit_limitations": [],
        "implicit_limitations": [],
        "variables": ["var1", "var2"]
    }
    
    paper_b = {
        "claims": ["Claim B1"],
        "methods": ["Method B"],
        "evidence": [],
        "explicit_limitations": [],
        "implicit_limitations": [],
        "variables": ["var2", "var3"]
    }
    
    agent = SynergyAgent()
    graph = agent._build_graph(paper_a, paper_b)
    
    # Check nodes
    nodes = graph.get("nodes", [])
    if len(nodes) < 5:  # At least 2 claims + 2 vars from A, 1 claim + 2 vars from B
        print(f"[FAIL] Too few nodes: {len(nodes)}")
        return False
    
    # Check edges
    edges = graph.get("edges", [])
    if len(edges) < 2:  # At least some edges from claims to variables
        print(f"[FAIL] Too few edges: {len(edges)}")
        return False
    
    # Check node IDs
    node_ids = [n["id"] for n in nodes]
    if "A_claim_1" not in node_ids or "B_claim_1" not in node_ids:
        print("[FAIL] Missing expected node IDs")
        return False
    
    print("[PASS] Graph structure correct!")
    print(f"   Nodes: {len(nodes)}")
    print(f"   Edges: {len(edges)}")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\nPHASE 2 TEST SUITE\n")
    
    results = []
    
    results.append(("Basic Analysis", test_basic_analysis()))
    results.append(("Input Validation", test_input_validation()))
    results.append(("Graph Structure", test_graph_structure()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result is True:
            print(f"[PASS] {test_name}: PASSED")
            passed += 1
        else:
            print(f"[FAIL] {test_name}: FAILED")
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n[SUCCESS] Phase 2 is working correctly!")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please review above.")
        return 1


if __name__ == "__main__":
    # Check API key
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "extraction", ".env"))
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        print("[WARNING] GROQ_API_KEY not set or is placeholder")
        print("   Set it in extraction/.env file")
        print("   Tests may fail without a valid API key\n")
    
    exit_code = run_all_tests()
    sys.exit(exit_code)

