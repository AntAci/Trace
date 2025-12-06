"""
Test Phase 4: Hypothesis Minting & Registry

Tests the minting service, registry store, and Neo client.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase4.minting_service import (
    validate_hypothesis_card,
    canonicalise_card,
    compute_hash,
    mint_hypothesis
)
from phase4.registry_store import save_hypothesis, get_hypothesis, list_hypotheses
from phase4.neo_client import write_hypothesis_receipt


# Use temporary directory for registry in tests
TEST_REGISTRY_DIR = None


def setup_test_registry():
    """Set up temporary registry directory for testing."""
    global TEST_REGISTRY_DIR
    TEST_REGISTRY_DIR = tempfile.mkdtemp()
    # Monkey patch registry_store to use test directory
    import phase4.registry_store as rs
    rs.REGISTRY_DIR = TEST_REGISTRY_DIR


def teardown_test_registry():
    """Clean up temporary registry directory."""
    global TEST_REGISTRY_DIR
    if TEST_REGISTRY_DIR and os.path.exists(TEST_REGISTRY_DIR):
        shutil.rmtree(TEST_REGISTRY_DIR)
    # Restore original registry directory
    import phase4.registry_store as rs
    rs.REGISTRY_DIR = "data/hypotheses"


def test_canonicalisation_is_deterministic():
    """Test that canonicalisation produces same output for same input."""
    print("=" * 60)
    print("TEST 1: Canonicalisation Determinism")
    print("=" * 60)
    
    card = {
        "hypothesis_id": "trace_hyp_001",
        "primary_synergy_id": "syn_1",
        "hypothesis": "Test hypothesis",
        "rationale": "Test rationale",
        "source_support": {
            "paper_B_claim_ids": ["B_claim_1"],
            "paper_A_claim_ids": ["A_claim_1"],
            "variables_used": ["temperature"]
        },
        "proposed_experiment": {
            "expected_direction": "increase",
            "description": "Test experiment",
            "measurements": ["measurement1"]
        },
        "confidence": "medium",
        "risk_notes": []
    }
    
    # Canonicalise twice (with different key order)
    canonical1 = canonicalise_card(card)
    
    # Reorder some nested dicts
    card["source_support"] = {
        "variables_used": ["temperature"],
        "paper_A_claim_ids": ["A_claim_1"],
        "paper_B_claim_ids": ["B_claim_1"]
    }
    canonical2 = canonicalise_card(card)
    
    if canonical1 != canonical2:
        print("[FAIL] Canonicalisation not deterministic")
        print(f"  First:  {canonical1[:100]}...")
        print(f"  Second: {canonical2[:100]}...")
        return False
    
    # Check hash is same
    hash1 = compute_hash(canonical1)
    hash2 = compute_hash(canonical2)
    
    if hash1 != hash2:
        print("[FAIL] Hash not deterministic")
        return False
    
    print("[PASS] Canonicalisation is deterministic")
    print(f"   Hash: {hash1[:20]}...")
    
    return True


def test_mint_rejects_invalid_card():
    """Test that minting rejects invalid HypothesisCard."""
    print("\n" + "=" * 60)
    print("TEST 2: Invalid Card Rejection")
    print("=" * 60)
    
    # Missing required field
    invalid_card = {
        "hypothesis_id": "trace_hyp_001",
        "primary_synergy_id": "syn_1"
        # Missing other required fields
    }
    
    try:
        validate_hypothesis_card(invalid_card)
        print("[FAIL] Should have raised ValueError for invalid card")
        return False
    except ValueError:
        print("[PASS] Correctly rejected invalid card")
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False
    
    # Missing nested field
    invalid_card2 = {
        "hypothesis_id": "trace_hyp_001",
        "primary_synergy_id": "syn_1",
        "hypothesis": "Test",
        "rationale": "Test",
        "source_support": {
            "paper_A_claim_ids": []
            # Missing paper_B_claim_ids and variables_used
        },
        "proposed_experiment": {
            "description": "Test",
            "measurements": [],
            "expected_direction": ""
        },
        "confidence": "medium",
        "risk_notes": []
    }
    
    try:
        validate_hypothesis_card(invalid_card2)
        print("[FAIL] Should have raised ValueError for missing nested fields")
        return False
    except ValueError:
        print("[PASS] Correctly rejected card with missing nested fields")
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False
    
    return True


def test_mint_writes_to_registry_and_neo():
    """Test that minting writes to both registry and Neo."""
    print("\n" + "=" * 60)
    print("TEST 3: Mint Writes to Registry and Neo")
    print("=" * 60)
    
    setup_test_registry()
    
    try:
        valid_card = {
            "hypothesis_id": "trace_hyp_test_mint",
            "primary_synergy_id": "syn_1",
            "hypothesis": "Test hypothesis",
            "rationale": "Test rationale",
            "source_support": {
                "paper_A_claim_ids": ["A_claim_1"],
                "paper_B_claim_ids": ["B_claim_1"],
                "variables_used": ["temperature"]
            },
            "proposed_experiment": {
                "description": "Test experiment",
                "measurements": ["measurement1"],
                "expected_direction": "increase"
            },
            "confidence": "medium",
            "risk_notes": []
        }
        
        result = mint_hypothesis(valid_card, author_wallet="NXXXX...")
        
        # Check MintResult structure
        required_fields = ["hypothesis_id", "content_hash", "neo_tx_id", "created_at", "version"]
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"[FAIL] MintResult missing fields: {missing_fields}")
            return False
        
        # Check registry
        retrieved = get_hypothesis("trace_hyp_test_mint")
        if not retrieved:
            print("[FAIL] Hypothesis not found in registry")
            return False
        
        if retrieved.get("content_hash") != result["content_hash"]:
            print("[FAIL] Content hash mismatch in registry")
            return False
        
        if retrieved.get("neo_tx_id") != result["neo_tx_id"]:
            print("[FAIL] Neo tx ID mismatch in registry")
            return False
        
        # Check that Neo was called (mock returns transaction ID)
        if not result["neo_tx_id"] or not result["neo_tx_id"].startswith("0x"):
            print("[FAIL] Invalid Neo transaction ID")
            return False
        
        print("[PASS] Minting writes to both registry and Neo")
        print(f"   Hypothesis ID: {result['hypothesis_id']}")
        print(f"   Content hash: {result['content_hash'][:20]}...")
        print(f"   Neo tx ID: {result['neo_tx_id'][:20]}...")
        
        return True
        
    finally:
        teardown_test_registry()


def test_round_trip_read():
    """Test round-trip: mint then retrieve."""
    print("\n" + "=" * 60)
    print("TEST 4: Round-Trip Read")
    print("=" * 60)
    
    setup_test_registry()
    
    try:
        original_card = {
            "hypothesis_id": "trace_hyp_roundtrip",
            "primary_synergy_id": "syn_1",
            "hypothesis": "Round-trip test hypothesis",
            "rationale": "Test rationale for round-trip",
            "source_support": {
                "paper_A_claim_ids": ["A_claim_1", "A_claim_2"],
                "paper_B_claim_ids": ["B_claim_1"],
                "variables_used": ["temperature", "voltage"]
            },
            "proposed_experiment": {
                "description": "Round-trip experiment",
                "measurements": ["measurement1", "measurement2"],
                "expected_direction": "non-linear effect"
            },
            "confidence": "high",
            "risk_notes": ["Risk note 1", "Risk note 2"]
        }
        
        # Mint
        mint_result = mint_hypothesis(original_card, author_wallet="NXXXX...")
        
        # Retrieve
        retrieved = get_hypothesis("trace_hyp_roundtrip")
        
        if not retrieved:
            print("[FAIL] Could not retrieve minted hypothesis")
            return False
        
        # Check all original fields are present
        for field in ["hypothesis_id", "primary_synergy_id", "hypothesis", "rationale",
                     "source_support", "proposed_experiment", "confidence", "risk_notes"]:
            if field not in retrieved:
                print(f"[FAIL] Missing field in retrieved card: {field}")
                return False
        
        # Check metadata was added
        if "content_hash" not in retrieved:
            print("[FAIL] Missing content_hash in retrieved card")
            return False
        
        if "created_at" not in retrieved:
            print("[FAIL] Missing created_at in retrieved card")
            return False
        
        if "neo_tx_id" not in retrieved:
            print("[FAIL] Missing neo_tx_id in retrieved card")
            return False
        
        # Verify content hash matches
        canonical = canonicalise_card(original_card)
        expected_hash = compute_hash(canonical)
        
        if retrieved["content_hash"] != expected_hash:
            print("[FAIL] Content hash mismatch")
            return False
        
        print("[PASS] Round-trip read successful")
        print(f"   Retrieved hypothesis: {retrieved['hypothesis_id']}")
        print(f"   Content hash matches: {retrieved['content_hash'] == expected_hash}")
        
        return True
        
    finally:
        teardown_test_registry()


def test_registry_filtering():
    """Test registry filtering functionality."""
    print("\n" + "=" * 60)
    print("TEST 5: Registry Filtering")
    print("=" * 60)
    
    setup_test_registry()
    
    try:
        # Create test hypotheses
        card1 = {
            "hypothesis_id": "trace_hyp_filter1",
            "primary_synergy_id": "syn_1",
            "hypothesis": "Test 1",
            "rationale": "Test",
            "source_support": {
                "paper_A_claim_ids": [],
                "paper_B_claim_ids": [],
                "variables_used": ["temperature"]
            },
            "proposed_experiment": {
                "description": "Test",
                "measurements": [],
                "expected_direction": ""
            },
            "confidence": "high",
            "risk_notes": []
        }
        
        card2 = {
            "hypothesis_id": "trace_hyp_filter2",
            "primary_synergy_id": "syn_2",
            "hypothesis": "Test 2",
            "rationale": "Test",
            "source_support": {
                "paper_A_claim_ids": [],
                "paper_B_claim_ids": [],
                "variables_used": ["voltage"]
            },
            "proposed_experiment": {
                "description": "Test",
                "measurements": [],
                "expected_direction": ""
            },
            "confidence": "medium",
            "risk_notes": []
        }
        
        save_hypothesis(card1)
        save_hypothesis(card2)
        
        # Test filter by variables
        filtered = list_hypotheses({"variables_used": ["temperature"]})
        if len(filtered) != 1 or filtered[0]["hypothesis_id"] != "trace_hyp_filter1":
            print("[FAIL] Variable filtering not working")
            return False
        
        # Test filter by confidence
        filtered = list_hypotheses({"confidence": "high"})
        if len(filtered) != 1 or filtered[0]["hypothesis_id"] != "trace_hyp_filter1":
            print("[FAIL] Confidence filtering not working")
            return False
        
        # Test filter by synergy_id
        filtered = list_hypotheses({"primary_synergy_id": "syn_2"})
        if len(filtered) != 1 or filtered[0]["hypothesis_id"] != "trace_hyp_filter2":
            print("[FAIL] Synergy ID filtering not working")
            return False
        
        print("[PASS] Registry filtering works correctly")
        
        return True
        
    finally:
        teardown_test_registry()


def run_all_tests():
    """Run all tests."""
    print("\nPHASE 4 TEST SUITE\n")
    
    results = []
    
    results.append(("Canonicalisation Determinism", test_canonicalisation_is_deterministic()))
    results.append(("Invalid Card Rejection", test_mint_rejects_invalid_card()))
    results.append(("Mint Writes to Registry and Neo", test_mint_writes_to_registry_and_neo()))
    results.append(("Round-Trip Read", test_round_trip_read()))
    results.append(("Registry Filtering", test_registry_filtering()))
    
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
        print("\n[SUCCESS] Phase 4 is working correctly!")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please review above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

