"""
Phase 4: Hypothesis Minting Service

Core logic for minting hypotheses to:
1. Off-chain registry (local JSON storage)
2. Neo blockchain (on-chain attestation)
3. NeoFS (decentralized storage) - SpoonOS Tool integration
4. X402 payment (micropayment protocol) - SpoonOS Tool integration

This module demonstrates the complete minting flow using official SpoonOS tools
to satisfy the hackathon requirement:
"Use at least one Tool module from the official Spoon-toolkit"
"""
import json
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from phase4.registry_store import save_hypothesis
from phase4.neo_client import write_hypothesis_receipt

# Import SpoonOS tool integrations
try:
    from phase4.spoon_tools import (
        SpoonToolManager,
        get_tool_manager,
        store_hypothesis_on_neofs,
        mint_with_payment,
        NEOFS_AVAILABLE,
        X402_AVAILABLE
    )
    SPOON_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"[Warning] SpoonOS tools not available: {e}")
    SPOON_TOOLS_AVAILABLE = False
    NEOFS_AVAILABLE = False
    X402_AVAILABLE = False


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


def mint_hypothesis(card: Dict[str, Any], author_wallet: str,
                    use_neofs: bool = True, use_x402: bool = False) -> Dict[str, Any]:
    """
    Mint a hypothesis to off-chain registry, Neo blockchain, and NeoFS.

    Process:
    1. Validate HypothesisCard
    2. Canonicalise JSON
    3. Compute content hash
    4. Enrich card with metadata
    5. Store in off-chain registry
    6. Write Neo transaction
    7. Store on NeoFS (SpoonOS Tool) - NEW
    8. Process X402 payment if enabled (SpoonOS Tool) - NEW
    9. Return MintResult

    Args:
        card: HypothesisCard JSON dict
        author_wallet: Author's wallet address
        use_neofs: Whether to store on NeoFS (default: True)
        use_x402: Whether to process X402 payment (default: False)

    Returns:
        dict: MintResult with all transaction IDs
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

    # =========================================================================
    # SpoonOS Tool Integrations (Hackathon Requirements)
    # =========================================================================

    neofs_result = None
    x402_result = None

    if SPOON_TOOLS_AVAILABLE and (use_neofs or use_x402):
        try:
            # Run async operations
            neofs_result, x402_result = _run_spoon_tools_async(
                enriched_card, author_wallet, use_neofs, use_x402
            )

            # Add NeoFS info to enriched card
            if neofs_result:
                enriched_card["neofs_object_id"] = neofs_result.get("object_id")
                enriched_card["neofs_container_id"] = neofs_result.get("container_id")

            # Add X402 payment info to enriched card
            if x402_result:
                enriched_card["x402_tx_hash"] = x402_result.get("tx_hash")
                enriched_card["x402_amount_usdc"] = x402_result.get("amount_usdc")
        except Exception as e:
            print(f"[Warning] SpoonOS tool integration failed: {e}")
            # Continue without NeoFS/X402 - not critical

    # Update registry with all metadata
    save_hypothesis(enriched_card)

    # Return MintResult
    result = {
        "hypothesis_id": card["hypothesis_id"],
        "content_hash": content_hash,
        "neo_tx_id": neo_tx_id,
        "created_at": enriched_card["created_at"],
        "version": "v1"
    }

    # Add SpoonOS tool results
    if neofs_result:
        result["neofs"] = {
            "object_id": neofs_result.get("object_id"),
            "container_id": neofs_result.get("container_id"),
            "success": neofs_result.get("success", False)
        }

    if x402_result:
        result["x402"] = {
            "tx_hash": x402_result.get("tx_hash"),
            "amount_usdc": x402_result.get("amount_usdc"),
            "network": x402_result.get("network"),
            "success": x402_result.get("success", False)
        }

    return result


def _run_spoon_tools_async(
    enriched_card: Dict[str, Any],
    author_wallet: str,
    use_neofs: bool,
    use_x402: bool
) -> tuple:
    """
    Run SpoonOS tool operations asynchronously.

    This helper handles the async-to-sync bridge for SpoonOS tools.
    """
    async def _async_operations():
        manager = get_tool_manager()
        await manager.initialize()

        neofs_result = None
        x402_result = None

        if use_neofs:
            print("[SpoonOS] Storing hypothesis on NeoFS...")
            neofs_result = await manager.store_hypothesis(enriched_card)
            print(f"[SpoonOS] NeoFS storage result: {neofs_result.get('success', False)}")

        if use_x402:
            print("[SpoonOS] Processing X402 payment...")
            x402_result = await manager.process_payment(
                hypothesis_id=enriched_card.get("hypothesis_id"),
                content_hash=enriched_card.get("content_hash"),
                author_wallet=author_wallet
            )
            print(f"[SpoonOS] X402 payment result: {x402_result.get('success', False)}")

        return neofs_result, x402_result

    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context - use create_task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _async_operations())
            return future.result(timeout=30)
    except RuntimeError:
        # No event loop running - we can use asyncio.run
        return asyncio.run(_async_operations())


async def mint_hypothesis_async(
    card: Dict[str, Any],
    author_wallet: str,
    use_neofs: bool = True,
    use_x402: bool = False
) -> Dict[str, Any]:
    """
    Async version of mint_hypothesis.

    Use this when calling from an async context for better performance.
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

    enriched_card["neo_tx_id"] = neo_tx_id

    # SpoonOS Tool Integrations
    neofs_result = None
    x402_result = None

    if SPOON_TOOLS_AVAILABLE:
        manager = get_tool_manager()
        await manager.initialize()

        if use_neofs:
            print("[SpoonOS] Storing hypothesis on NeoFS...")
            neofs_result = await manager.store_hypothesis(enriched_card)
            if neofs_result:
                enriched_card["neofs_object_id"] = neofs_result.get("object_id")
                enriched_card["neofs_container_id"] = neofs_result.get("container_id")

        if use_x402:
            print("[SpoonOS] Processing X402 payment...")
            x402_result = await manager.process_payment(
                hypothesis_id=enriched_card.get("hypothesis_id"),
                content_hash=enriched_card.get("content_hash"),
                author_wallet=author_wallet
            )
            if x402_result:
                enriched_card["x402_tx_hash"] = x402_result.get("tx_hash")

    # Update registry
    save_hypothesis(enriched_card)

    # Build result
    result = {
        "hypothesis_id": card["hypothesis_id"],
        "content_hash": content_hash,
        "neo_tx_id": neo_tx_id,
        "created_at": enriched_card["created_at"],
        "version": "v1"
    }

    if neofs_result:
        result["neofs"] = {
            "object_id": neofs_result.get("object_id"),
            "container_id": neofs_result.get("container_id"),
            "success": neofs_result.get("success", False)
        }

    if x402_result:
        result["x402"] = {
            "tx_hash": x402_result.get("tx_hash"),
            "amount_usdc": x402_result.get("amount_usdc"),
            "success": x402_result.get("success", False)
        }

    return result


if __name__ == "__main__":
    # Example usage demonstrating SpoonOS tool integrations
    print("=" * 60)
    print("Hypothesis Minting Service - SpoonOS Tool Demo")
    print("=" * 60)

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

    print("\nSpoonOS Tool Availability:")
    print(f"  NeoFS Tools: {NEOFS_AVAILABLE}")
    print(f"  X402 Tools: {X402_AVAILABLE}")
    print(f"  SpoonOS Integration: {SPOON_TOOLS_AVAILABLE}")

    try:
        print("\n" + "-" * 60)
        print("Minting hypothesis with SpoonOS tools...")
        print("-" * 60)

        result = mint_hypothesis(
            card=example_card,
            author_wallet="NTestWallet123",
            use_neofs=True,   # Enable NeoFS storage
            use_x402=False    # Disable X402 payment (enable for testing)
        )

        print("\n" + "=" * 60)
        print("Mint Result:")
        print("=" * 60)
        print(json.dumps(result, indent=2))

        print("\n[SUCCESS] Minting completed with SpoonOS tool integrations!")

    except Exception as e:
        print(f"\n[ERROR] Minting failed: {e}")
        import traceback
        traceback.print_exc()

