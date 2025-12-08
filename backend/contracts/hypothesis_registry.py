"""
Trace Hypothesis Registry Smart Contract

A Neo N3 smart contract for storing hypothesis attestations on-chain.
Stores mapping of hypothesis_id -> (content_hash, author, timestamp)

Compile with: neo3-boa compile contracts/hypothesis_registry.py
Deploy the generated .nef and .manifest.json to Neo N3 testnet/mainnet
"""
from typing import Any

from boa3.sc import runtime, storage
from boa3.sc.compiletime import NeoMetadata, public
from boa3.sc.types import UInt160


# Contract metadata
def manifest() -> NeoMetadata:
    """Contract metadata for the manifest file."""
    meta = NeoMetadata()
    meta.author = "Trace Hackathon Team"
    meta.email = "trace@hackathon.dev"
    meta.description = "Hypothesis Registry for Trace - stores scientific hypothesis attestations on Neo blockchain"
    meta.version = "1.0.0"
    return meta


# Storage key prefixes
HASH_PREFIX = b'hash_'       # hypothesis_id -> content_hash
AUTHOR_PREFIX = b'author_'   # hypothesis_id -> author address
TIME_PREFIX = b'time_'       # hypothesis_id -> timestamp
COUNT_KEY = b'total_count'   # Total number of registered hypotheses
OWNER_KEY = b'owner'         # Contract owner


@public
def _deploy(data: Any, update: bool):
    """
    Called when contract is deployed or updated.
    Sets the contract owner to the transaction sender.
    """
    if not update:
        # Initial deployment - set owner
        owner = runtime.calling_script_hash
        storage.put_uint160(OWNER_KEY, owner)
        storage.put_int(COUNT_KEY, 0)


@public
def register(hypothesis_id: bytes, content_hash: str, author: UInt160) -> bool:
    """
    Register a new hypothesis attestation.

    Args:
        hypothesis_id: Unique identifier for the hypothesis as bytes (e.g., b"trace_hyp_abc123")
        content_hash: SHA-256 hash of the hypothesis content (e.g., "0x...")
        author: Neo address (UInt160) of the hypothesis author

    Returns:
        bool: True if registration successful, False if hypothesis_id already exists
    """
    # Build storage key
    hash_key = HASH_PREFIX + hypothesis_id

    # Check if hypothesis already registered
    existing = storage.get(hash_key)
    if len(existing) > 0:
        # Hypothesis already exists
        return False

    # Get current timestamp
    timestamp = runtime.time

    # Store hypothesis data
    storage.put_str(hash_key, content_hash)
    storage.put_uint160(AUTHOR_PREFIX + hypothesis_id, author)
    storage.put_int(TIME_PREFIX + hypothesis_id, timestamp)

    # Increment counter
    count = storage.get_int(COUNT_KEY)
    storage.put_int(COUNT_KEY, count + 1)

    # Fire event for indexing (using simple notification)
    runtime.notify('HypothesisRegistered')

    return True


@public(safe=True)
def get_hash(hypothesis_id: bytes) -> str:
    """
    Get the content hash for a registered hypothesis.

    Args:
        hypothesis_id: The hypothesis ID to lookup (as bytes)

    Returns:
        str: The content hash, or empty string if not found
    """
    hash_key = HASH_PREFIX + hypothesis_id
    return storage.get_str(hash_key)


@public(safe=True)
def get_author(hypothesis_id: bytes) -> UInt160:
    """
    Get the author address for a registered hypothesis.

    Args:
        hypothesis_id: The hypothesis ID to lookup (as bytes)

    Returns:
        UInt160: The author's Neo address, or empty if not found
    """
    author_key = AUTHOR_PREFIX + hypothesis_id
    return storage.get_uint160(author_key)


@public(safe=True)
def get_timestamp(hypothesis_id: bytes) -> int:
    """
    Get the registration timestamp for a hypothesis.

    Args:
        hypothesis_id: The hypothesis ID to lookup (as bytes)

    Returns:
        int: Unix timestamp of registration, or 0 if not found
    """
    time_key = TIME_PREFIX + hypothesis_id
    return storage.get_int(time_key)


@public(safe=True)
def verify(hypothesis_id: bytes, expected_hash: str) -> bool:
    """
    Verify that a hypothesis exists and matches the expected hash.

    Args:
        hypothesis_id: The hypothesis ID to verify (as bytes)
        expected_hash: The expected content hash

    Returns:
        bool: True if hypothesis exists and hash matches
    """
    stored_hash = get_hash(hypothesis_id)

    if len(stored_hash) == 0:
        return False

    return stored_hash == expected_hash


@public(safe=True)
def exists(hypothesis_id: bytes) -> bool:
    """
    Check if a hypothesis ID is registered.

    Args:
        hypothesis_id: The hypothesis ID to check (as bytes)

    Returns:
        bool: True if registered
    """
    hash_key = HASH_PREFIX + hypothesis_id
    result = storage.get(hash_key)
    return len(result) > 0


@public(safe=True)
def total_count() -> int:
    """
    Get the total number of registered hypotheses.

    Returns:
        int: Total count
    """
    return storage.get_int(COUNT_KEY)


@public(safe=True)
def get_owner() -> UInt160:
    """
    Get the contract owner address.

    Returns:
        UInt160: Owner's Neo address
    """
    return storage.get_uint160(OWNER_KEY)
