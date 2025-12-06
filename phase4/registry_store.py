"""
Phase 4: Off-Chain Registry Store

Simple file-based storage for HypothesisCards.
"""
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


REGISTRY_DIR = "data/hypotheses"


def _ensure_registry_dir():
    """Ensure the registry directory exists."""
    Path(REGISTRY_DIR).mkdir(parents=True, exist_ok=True)


def save_hypothesis(card: Dict[str, Any]) -> None:
    """
    Save a HypothesisCard to the off-chain registry.
    
    Stores as JSON file: data/hypotheses/{hypothesis_id}.json
    
    Args:
        card: HypothesisCard dict (may include metadata like content_hash, created_at, etc.)
    """
    _ensure_registry_dir()
    
    hypothesis_id = card.get("hypothesis_id")
    if not hypothesis_id:
        raise ValueError("HypothesisCard must have hypothesis_id")
    
    file_path = os.path.join(REGISTRY_DIR, f"{hypothesis_id}.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
    
    print(f"[Registry] Saved hypothesis {hypothesis_id} to {file_path}")


def get_hypothesis(hypothesis_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a HypothesisCard from the registry.
    """
    file_path = os.path.join(REGISTRY_DIR, f"{hypothesis_id}.json")
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_hypotheses(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    List all hypotheses in the registry, optionally filtered.
    """
    _ensure_registry_dir()
    
    if not os.path.exists(REGISTRY_DIR):
        return []
    
    hypotheses = []
    
    # Load all hypothesis files
    for filename in os.listdir(REGISTRY_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(REGISTRY_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    card = json.load(f)
                    hypotheses.append(card)
            except Exception as e:
                print(f"[Warning] Failed to load {filename}: {e}")
                continue
    
    # Apply filters if provided
    if filters:
        filtered = []
        
        for card in hypotheses:
            # Filter by variables_used
            if "variables_used" in filters:
                card_vars = set(card.get("source_support", {}).get("variables_used", []))
                filter_vars = set(filters["variables_used"])
                if not card_vars.intersection(filter_vars):
                    continue
            
            # Filter by primary_synergy_id
            if "primary_synergy_id" in filters:
                if card.get("primary_synergy_id") != filters["primary_synergy_id"]:
                    continue
            
            # Filter by confidence
            if "confidence" in filters:
                if card.get("confidence") != filters["confidence"]:
                    continue
            
            filtered.append(card)
        
        return filtered
    
    return hypotheses


if __name__ == "__main__":
    # Example usage
    test_card = {
        "hypothesis_id": "trace_hyp_test",
        "primary_synergy_id": "syn_1",
        "hypothesis": "Test hypothesis",
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
        "confidence": "medium",
        "risk_notes": []
    }
    
    save_hypothesis(test_card)
    retrieved = get_hypothesis("trace_hyp_test")
    print(f"Retrieved: {retrieved is not None}")
    
    all_hypotheses = list_hypotheses()
    print(f"Total hypotheses: {len(all_hypotheses)}")
    
    filtered = list_hypotheses({"variables_used": ["temperature"]})
    print(f"Filtered by temperature: {len(filtered)}")

