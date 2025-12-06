"""
Phase 4: Hypothesis Minting Service

Core logic for minting hypotheses to off-chain registry and Neo blockchain.
"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from phase4.registry_store import save_hypothesis
from phase4.neo_client import write_hypothesis_receipt


def validate_hypothesis_card(card: Dict[str, Any]) -> None:
    """
    Validate that a HypothesisCard has all required fields.
    
    Args:
        card: HypothesisCard JSON dict
    
    Raises:
        ValueError: If required fields are missing
    """
    required_fields = [
        "hypothesis_id",
        "primary_synergy_id",
        "hypothesis",
        "rationale",
        "source_support",
        "proposed_experiment",
        "confidence",
        "risk_notes"
    ]
    
    missing_fields = [f for f in required_fields if f not in card]
    if missing_fields:
        raise ValueError(f"HypothesisCard missing required fields: {missing_fields}")
    
    # Validate nested structures
    source_support = card.get("source_support", {})
    if not isinstance(source_support, dict):
        raise ValueError("source_support must be a dict")
    
    required_source_fields = ["paper_A_claim_ids", "paper_B_claim_ids", "variables_used"]
    missing_source_fields = [f for f in required_source_fields if f not in source_support]
    if missing_source_fields:
        raise ValueError(f"source_support missing required fields: {missing_source_fields}")
    
    proposed_experiment = card.get("proposed_experiment", {})
    if not isinstance(proposed_experiment, dict):
        raise ValueError("proposed_experiment must be a dict")
    
    required_experiment_fields = ["description", "measurements", "expected_direction"]
    missing_experiment_fields = [f for f in required_experiment_fields if f not in proposed_experiment]
    if missing_experiment_fields:
        raise ValueError(f"proposed_experiment missing required fields: {missing_experiment_fields}")


def canonicalise_card(card: Dict[str, Any]) -> str:
    """
    Canonicalise HypothesisCard JSON to deterministic string.
    
    - Sorts all keys recursively
    - Removes any extra metadata fields (content_hash, created_at, version, neo_tx_id)
    - Returns canonical JSON string
    """
    # Create a copy to avoid modifying original
    canonical = {}
    
    # Only include core HypothesisCard fields (exclude minting metadata)
    core_fields = [
        "hypothesis_id",
        "primary_synergy_id",
        "hypothesis",
        "rationale",
        "source_support",
        "proposed_experiment",
        "confidence",
        "risk_notes"
    ]
    
    for field in core_fields:
        if field in card:
            canonical[field] = card[field]
    
    # Recursively sort nested dicts
    def sort_dict_recursive(d):
        if isinstance(d, dict):
            return {k: sort_dict_recursive(v) for k, v in sorted(d.items())}
        elif isinstance(d, list):
            return [sort_dict_recursive(item) for item in d]
        else:
            return d
    
    canonical_sorted = sort_dict_recursive(canonical)
    
    # Return as compact JSON (no extra whitespace)
    return json.dumps(canonical_sorted, separators=(',', ':'), ensure_ascii=False)


def compute_hash(canonical_json: str) -> str:
    """
    Compute SHA-256 hash of canonical JSON.
    
    Args:
        canonical_json: Canonical JSON string
    
    Returns:
        str: Hex hash prefixed with "0x"
    """
    hash_bytes = hashlib.sha256(canonical_json.encode('utf-8')).digest()
    return "0x" + hash_bytes.hex()


def mint_hypothesis(card: Dict[str, Any], author_wallet: str) -> Dict[str, Any]:
    """
    Mint a hypothesis to off-chain registry and Neo blockchain.
    
    Process:
    1. Validate HypothesisCard
    2. Canonicalise JSON
    3. Compute content hash
    4. Enrich card with metadata
    5. Store in off-chain registry
    6. Write Neo transaction
    7. Return MintResult
    """
    # Validate
    validate_hypothesis_card(card)
    
    # Canonicalise
    canonical_json = canonicalise_card(card)
    
    # Compute hash
    content_hash = compute_hash(canonical_json)
    
    # Enrich card with metadata
    enriched_card = card.copy()
    enriched_card["content_hash"] = content_hash
    enriched_card["created_at"] = datetime.now(timezone.utc).isoformat()
    enriched_card["version"] = "v1"
    enriched_card["author_wallet"] = author_wallet
    
    # Store in off-chain registry
    save_hypothesis(enriched_card)
    
    # Write to Neo blockchain
    neo_tx_id = write_hypothesis_receipt(
        hypothesis_id=card["hypothesis_id"],
        content_hash=content_hash,
        author_wallet=author_wallet
    )
    
    # Add Neo transaction ID to enriched card
    enriched_card["neo_tx_id"] = neo_tx_id
    
    # Update registry with Neo tx ID
    save_hypothesis(enriched_card)
    
    # Return MintResult
    return {
        "hypothesis_id": card["hypothesis_id"],
        "content_hash": content_hash,
        "neo_tx_id": neo_tx_id,
        "created_at": enriched_card["created_at"],
        "version": "v1"
    }


if __name__ == "__main__":
    # Example usage
    example_card = {
        "hypothesis_id": "trace_hyp_001",
        "primary_synergy_id": "syn_1",
        "hypothesis": "If X then Y",
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
    
    try:
        result = mint_hypothesis(example_card, author_wallet="NXXXX...")
        print("Mint successful!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

