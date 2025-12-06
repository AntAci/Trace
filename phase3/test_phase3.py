"""
Test Phase 3: Hypothesis Generation

Tests the HypothesisAgent with sample Phase 1 and Phase 2 outputs.
"""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase3.hypothesis_agent import HypothesisAgent, generate_hypothesis


def test_hypothesis_generation():
    """Test hypothesis generation from Phase 1 and Phase 2 outputs."""
    print("=" * 60)
    print("TEST 1: Hypothesis Generation")
    print("=" * 60)
    
    # Phase 1 outputs
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
    
    # Phase 2 output
    synergy_result = {
        "overlapping_variables": ["temperature"],
        "potential_synergies": [
            {
                "id": "syn_1",
                "description": "Paper A's findings on non-linear capacity fade above 45°C could refine Paper B's linear aging model",
                "paper_A_support": ["A_claim_1", "A_claim_2"],
                "paper_B_support": ["B_claim_1", "B_claim_2"]
            }
        ],
        "potential_conflicts": [
            {
                "id": "conf_1",
                "description": "Paper A's evidence of non-linear behavior contradicts Paper B's linear assumption",
                "paper_A_support": ["A_claim_2"],
                "paper_B_support": ["B_claim_2"]
            }
        ],
        "graph": {
            "nodes": [
                {"id": "A_claim_1", "type": "claim", "paper": "A", "text": "High temperature accelerates battery degradation"},
                {"id": "A_claim_2", "type": "claim", "paper": "A", "text": "Non-linear capacity fade occurs above 45°C"},
                {"id": "B_claim_1", "type": "claim", "paper": "B", "text": "State of health can be predicted using temperature and voltage"},
                {"id": "B_claim_2", "type": "claim", "paper": "B", "text": "Linear aging model works well for most operating conditions"},
                {"id": "var_temperature", "type": "variable", "paper": "both", "text": "temperature"}
            ],
            "edges": [
                {"source": "A_claim_1", "target": "var_temperature", "relation": "uses_variable"},
                {"source": "B_claim_1", "target": "var_temperature", "relation": "uses_variable"},
                {"source": "A_claim_1", "target": "B_claim_1", "relation": "potential_synergy", "synergy_id": "syn_1"}
            ]
        }
    }
    
    try:
        result = generate_hypothesis(paper_a, paper_b, synergy_result)
        
        # Validate structure
        required_fields = [
            "hypothesis_id", "primary_synergy_id", "hypothesis", "rationale",
            "source_support", "proposed_experiment", "confidence", "risk_notes"
        ]
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"[FAIL] Missing fields: {missing_fields}")
            return False
        
        # Validate nested structures
        source_support = result.get("source_support", {})
        if not isinstance(source_support, dict):
            print("[FAIL] source_support must be a dict")
            return False
        
        if "paper_A_claim_ids" not in source_support or "paper_B_claim_ids" not in source_support:
            print("[FAIL] source_support missing required fields")
            return False
        
        proposed_experiment = result.get("proposed_experiment", {})
        if not isinstance(proposed_experiment, dict):
            print("[FAIL] proposed_experiment must be a dict")
            return False
        
        if "description" not in proposed_experiment or "measurements" not in proposed_experiment:
            print("[FAIL] proposed_experiment missing required fields")
            return False
        
        # Validate hypothesis quality
        hypothesis = result.get("hypothesis", "")
        if not hypothesis or len(hypothesis) < 20:
            print("[FAIL] Hypothesis too short or empty")
            return False
        
        if "if" not in hypothesis.lower() and "then" not in hypothesis.lower():
            print("[FAIL] Hypothesis should be in 'if-then' format")
            return False
        
        # Validate claim references
        rationale = result.get("rationale", "")
        if "A_claim" not in rationale and "B_claim" not in rationale:
            print("[WARNING] Rationale may not reference specific claims")
        
        print("[PASS] Hypothesis generation successful!")
        print(f"   Hypothesis ID: {result.get('hypothesis_id', 'N/A')}")
        print(f"   Primary synergy: {result.get('primary_synergy_id', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"   Paper A claims referenced: {len(source_support.get('paper_A_claim_ids', []))}")
        print(f"   Paper B claims referenced: {len(source_support.get('paper_B_claim_ids', []))}")
        print(f"   Variables used: {len(source_support.get('variables_used', []))}")
        
        print("\nHypothesis:")
        print(f"  {result.get('hypothesis', 'N/A')}")
        
        print("\nFull output (first 1000 chars):")
        print(json.dumps(result, indent=2)[:1000] + "...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Hypothesis generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_semantic_grounding():
    """Test semantic grounding validation (no hallucination check)."""
    print("\n" + "=" * 60)
    print("TEST 2: Semantic Grounding Validation")
    print("=" * 60)
    
    agent = HypothesisAgent()
    
    paper_a = {
        "claims": ["Claim A1"],
        "methods": ["Method A"],
        "evidence": [],
        "explicit_limitations": [],
        "implicit_limitations": [],
        "variables": ["temperature", "voltage"]
    }
    
    paper_b = {
        "claims": ["Claim B1"],
        "methods": ["Method B"],
        "evidence": [],
        "explicit_limitations": [],
        "implicit_limitations": [],
        "variables": ["pressure", "current"]
    }
    
    synergy_result = {
        "overlapping_variables": [],
        "potential_synergies": [
            {
                "id": "syn_1",
                "description": "Test synergy",
                "paper_A_support": ["A_claim_1"],
                "paper_B_support": ["B_claim_1"]
            }
        ],
        "potential_conflicts": [],
        "graph": {
            "nodes": [
                {"id": "A_claim_1", "type": "claim", "paper": "A", "text": "Claim A1"},
                {"id": "B_claim_1", "type": "claim", "paper": "B", "text": "Claim B1"}
            ],
            "edges": []
        }
    }
    
    # Create hypothesis card with invalid references (hallucinated)
    invalid_hypothesis = {
        "primary_synergy_id": "syn_1",
        "hypothesis": "Test hypothesis",
        "rationale": "Test rationale",
        "source_support": {
            "paper_A_claim_ids": ["A_claim_1", "A_claim_99"],  # A_claim_99 doesn't exist
            "paper_B_claim_ids": ["B_claim_1"],
            "variables_used": ["temperature", "nonexistent_var"]  # nonexistent_var doesn't exist
        },
        "proposed_experiment": {
            "description": "Test experiment",
            "measurements": ["measurement1"],
            "expected_direction": "increase"
        },
        "confidence": "medium",
        "risk_notes": []
    }
    
    # Test validation
    validation_result = agent._validate_semantic_grounding(
        invalid_hypothesis, paper_a, paper_b, synergy_result
    )
    
    if validation_result["valid"]:
        print("[FAIL] Should have detected invalid references")
        return False
    
    if len(validation_result.get("errors", [])) == 0:
        print("[FAIL] Should have reported errors")
        return False
    
    print("[PASS] Correctly detected invalid references")
    print(f"   Errors found: {len(validation_result['errors'])}")
    
    # Test fixing
    fixed_hypothesis = agent._fix_hypothesis_card(
        invalid_hypothesis.copy(), validation_result, paper_a, paper_b, synergy_result
    )
    
    # Check that invalid references were removed
    if "A_claim_99" in fixed_hypothesis["source_support"]["paper_A_claim_ids"]:
        print("[FAIL] Invalid claim ID should have been removed")
        return False
    
    if "nonexistent_var" in fixed_hypothesis["source_support"]["variables_used"]:
        print("[FAIL] Invalid variable should have been removed")
        return False
    
    print("[PASS] Correctly fixed invalid references")
    
    return True


def test_input_validation():
    """Test input validation."""
    print("\n" + "=" * 60)
    print("TEST 2: Input Validation")
    print("=" * 60)
    
    agent = HypothesisAgent()
    
    valid_paper = {
        "claims": ["Test"],
        "methods": ["Test method"],
        "evidence": [],
        "explicit_limitations": [],
        "implicit_limitations": [],
        "variables": []
    }
    
    valid_synergy = {
        "overlapping_variables": [],
        "potential_synergies": [],
        "potential_conflicts": [],
        "graph": {"nodes": [], "edges": []}
    }
    
    # Test missing Phase 1 fields
    invalid_paper = {
        "claims": ["Test"]
        # Missing other required fields
    }
    
    try:
        agent.generate_hypothesis(invalid_paper, valid_paper, valid_synergy)
        print("[FAIL] Should have raised ValueError for invalid Phase 1 input")
        return False
    except ValueError:
        print("[PASS] Correctly rejected invalid Phase 1 input")
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False
    
    # Test missing Phase 2 fields
    invalid_synergy = {
        "potential_synergies": []
        # Missing other required fields
    }
    
    try:
        agent.generate_hypothesis(valid_paper, valid_paper, invalid_synergy)
        print("[FAIL] Should have raised ValueError for invalid Phase 2 input")
        return False
    except ValueError:
        print("[PASS] Correctly rejected invalid Phase 2 input")
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\nPHASE 3 TEST SUITE\n")
    
    results = []
    
    results.append(("Hypothesis Generation", test_hypothesis_generation()))
    results.append(("Semantic Grounding", test_semantic_grounding()))
    results.append(("Input Validation", test_input_validation()))
    
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
        print("\n[SUCCESS] Phase 3 is working correctly!")
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

