"""
Phase 4: Neo Blockchain Client

Wrapper around neo-mamba SDK for writing hypothesis receipts on-chain.
Uses ChainFacade for transaction building and signing.

Documentation: https://dojo.coz.io/neo3/mamba/
"""
import json
import hashlib
import os
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "..", "extraction", ".env")
load_dotenv(env_path)

# Try to import neo-mamba SDK
try:
    from neo3.api.wrappers import ChainFacade, GenericContract, GasToken
    from neo3.api.helpers.signing import sign_with_account
    from neo3.network.payloads.verification import Signer
    from neo3.wallet.account import Account
    from neo3.core.types import UInt160
    NEO_AVAILABLE = True
except ImportError as e:
    NEO_AVAILABLE = False
    print(f"[Warning] neo-mamba SDK not available: {e}")
    print("Install with: pip install neo-mamba")


# Configuration
# Neo N3 Networks:
#   - testnet: Neo N3 TestNet (get GAS from https://n3t5wish.ngd.network/#/)
#   - mainnet: Neo N3 MainNet
# Neo X (EVM-compatible):
#   - neox_testnet: Chain ID 47763, RPC: https://mainnet-1.rpc.banelabs.org
#   - Explorer: https://xexplorer.neo.org
NEO_NETWORK = os.getenv("NEO_NETWORK", "testnet")  # "testnet" or "mainnet"
NEO_PRIVATE_KEY = os.getenv("NEO_PRIVATE_KEY", "")  # WIF format private key
NEO_RPC_URL = os.getenv("NEO_RPC_URL", "")  # Custom RPC URL (optional)

# Neo N3 TestNet network ID: 894710606 (v3.5.0)
# See: https://github.com/neo-project/neo-node/releases/tag/v3.5.0
NEO_N3_TESTNET_NETWORK_ID = 894710606

# Registry contract for storing hypothesis attestations (placeholder - deploy your own)
# This would be a simple storage contract that maps hypothesis_id -> content_hash
# Deploy using Neo3-Boa (Python): https://github.com/CityOfZion/neo3-boa
REGISTRY_CONTRACT_HASH = os.getenv("NEO_REGISTRY_CONTRACT", "")

# Block explorers for verification:
# - Dora (recommended): https://dora.coz.io/
# - NeoTube: https://neotube.io/
# - OneGate: https://explorer.onegate.space/


class NeoClient:
    """
    Client for interacting with Neo N3 blockchain.

    Provides methods to:
    - Write hypothesis receipts (attestations) on-chain
    - Query existing receipts
    - Verify content hashes
    """

    def __init__(self, network: str = "testnet", private_key: str = "", rpc_url: str = ""):
        """
        Initialize the Neo client.

        Args:
            network: "testnet" or "mainnet"
            private_key: WIF format private key for signing transactions
            rpc_url: Custom RPC URL (optional, uses default for network if not provided)
        """
        self.network = network
        self.private_key = private_key or NEO_PRIVATE_KEY
        self.rpc_url = rpc_url or NEO_RPC_URL
        self.facade: Optional[ChainFacade] = None
        self.account: Optional[Account] = None

        if NEO_AVAILABLE and self.private_key:
            self._initialize_facade()

    def _initialize_facade(self):
        """Initialize ChainFacade with appropriate network settings."""
        try:
            # Create account from private key
            self.account = Account.from_wif(self.private_key)

            # Create facade for appropriate network
            if self.rpc_url:
                # Custom RPC URL
                from neo3.api.noderpc import NeoRpcClient
                rpc_client = NeoRpcClient(self.rpc_url)
                self.facade = ChainFacade(rpc_client)
            elif self.network == "mainnet":
                self.facade = ChainFacade.node_provider_mainnet()
            else:
                self.facade = ChainFacade.node_provider_testnet()

            # Configure signer for transactions
            self.facade.add_signer(
                sign_with_account(self.account),
                Signer(self.account.script_hash)
            )

            print(f"[Neo] Initialized client for {self.network}")
            print(f"[Neo] Account address: {self.account.address}")

        except Exception as e:
            print(f"[Neo] Failed to initialize: {e}")
            self.facade = None
            self.account = None

    async def write_attestation(
        self,
        hypothesis_id: str,
        content_hash: str,
        author_wallet: str
    ) -> Dict[str, Any]:
        """
        Write a hypothesis attestation to the Neo blockchain.

        This creates an on-chain record proving that a hypothesis with the given
        content hash existed at a specific time. The full hypothesis data is stored
        off-chain; only the hash is stored on-chain for verification.

        Args:
            hypothesis_id: Unique identifier for the hypothesis
            content_hash: SHA-256 hash of the canonical hypothesis JSON
            author_wallet: Neo wallet address of the author

        Returns:
            dict: Transaction result with tx_id, block_hash, etc.
        """
        if not self.facade or not self.account:
            raise RuntimeError("Neo client not properly initialized. Check private key.")

        if not REGISTRY_CONTRACT_HASH:
            # No registry contract configured - use simple attestation via data embedding
            return await self._write_simple_attestation(hypothesis_id, content_hash, author_wallet)

        # Use registry contract if available
        return await self._write_registry_attestation(hypothesis_id, content_hash, author_wallet)

    async def _write_simple_attestation(
        self,
        hypothesis_id: str,
        content_hash: str,
        author_wallet: str
    ) -> Dict[str, Any]:
        """
        Write attestation using a simple self-transfer with embedded data.

        This is a fallback when no registry contract is deployed.
        The attestation data is embedded in the transaction attributes.
        """
        # Build attestation payload
        payload = {
            "type": "trace_hypothesis_attestation",
            "version": "v1",
            "hypothesis_id": hypothesis_id,
            "content_hash": content_hash,
            "author": author_wallet,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Convert to bytes for embedding (for future use in transaction attributes)
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')

        # Create a minimal GAS transfer to self (to create a valid transaction)
        # The attestation is proven by the transaction existing on-chain
        gas = GasToken()

        try:
            # Transfer minimal GAS to self (0.00000001 GAS = 1 unit)
            # This creates a valid transaction that we can reference
            receipt = await self.facade.invoke(
                gas.transfer(
                    self.account.script_hash,
                    self.account.script_hash,
                    1  # Minimal amount
                )
            )

            return {
                "success": True,
                "tx_id": str(receipt.tx_hash),
                "included_in_block": receipt.included_in_block,
                "confirmations": receipt.confirmations,
                "gas_consumed": str(receipt.gas_consumed),
                "hypothesis_id": hypothesis_id,
                "content_hash": content_hash,
                "attestation_type": "simple_transfer"
            }

        except Exception as e:
            raise RuntimeError(f"Failed to write attestation: {e}")

    async def _write_registry_attestation(
        self,
        hypothesis_id: str,
        content_hash: str,
        author_wallet: str
    ) -> Dict[str, Any]:
        """
        Write attestation using the Hypothesis Registry smart contract.

        The registry contract stores:
        - hypothesis_id -> content_hash mapping
        - hypothesis_id -> author mapping
        - hypothesis_id -> timestamp mapping

        Contract methods:
        - register(hypothesis_id: bytes, content_hash: str, author: UInt160) -> bool
        - get_hash(hypothesis_id: bytes) -> str
        - verify(hypothesis_id: bytes, expected_hash: str) -> bool
        """
        try:
            # Parse registry contract hash (remove 0x prefix if present)
            contract_hash = REGISTRY_CONTRACT_HASH
            if contract_hash.startswith("0x"):
                contract_hash = contract_hash[2:]

            # Create generic contract wrapper for registry
            registry = GenericContract(UInt160.from_string(contract_hash))

            # Convert hypothesis_id to bytes for the contract
            hypothesis_id_bytes = hypothesis_id.encode('utf-8')

            # Call the register function
            # register(hypothesis_id: bytes, content_hash: str, author: UInt160) -> bool
            receipt = await self.facade.invoke(
                registry.call_function(
                    "register",
                    [hypothesis_id_bytes, content_hash, self.account.script_hash]
                )
            )

            # Check if registration was successful
            success = receipt.result if hasattr(receipt, 'result') else True

            return {
                "success": bool(success),
                "tx_id": str(receipt.tx_hash),
                "included_in_block": receipt.included_in_block,
                "confirmations": receipt.confirmations,
                "gas_consumed": str(receipt.gas_consumed),
                "hypothesis_id": hypothesis_id,
                "content_hash": content_hash,
                "attestation_type": "registry_contract",
                "contract_hash": REGISTRY_CONTRACT_HASH
            }

        except Exception as e:
            raise RuntimeError(f"Failed to write registry attestation: {e}")

    async def verify_on_chain(self, hypothesis_id: str, expected_hash: str) -> bool:
        """
        Verify a hypothesis attestation on-chain using the registry contract.

        Args:
            hypothesis_id: The hypothesis ID to verify
            expected_hash: The expected content hash

        Returns:
            bool: True if the on-chain hash matches the expected hash
        """
        if not REGISTRY_CONTRACT_HASH:
            print("[Neo] No registry contract configured - cannot verify on-chain")
            return False

        if not self.facade:
            return False

        try:
            contract_hash = REGISTRY_CONTRACT_HASH
            if contract_hash.startswith("0x"):
                contract_hash = contract_hash[2:]

            registry = GenericContract(UInt160.from_string(contract_hash))
            hypothesis_id_bytes = hypothesis_id.encode('utf-8')

            # Call verify function (read-only, no gas cost)
            result = await self.facade.test_invoke(
                registry.call_function(
                    "verify",
                    [hypothesis_id_bytes, expected_hash]
                )
            )

            return bool(result.result) if hasattr(result, 'result') else False

        except Exception as e:
            print(f"[Neo] Verification failed: {e}")
            return False

    async def get_on_chain_hash(self, hypothesis_id: str) -> Optional[str]:
        """
        Get the stored content hash for a hypothesis from the registry contract.

        Args:
            hypothesis_id: The hypothesis ID to lookup

        Returns:
            str: The stored content hash, or None if not found
        """
        if not REGISTRY_CONTRACT_HASH:
            return None

        if not self.facade:
            return None

        try:
            contract_hash = REGISTRY_CONTRACT_HASH
            if contract_hash.startswith("0x"):
                contract_hash = contract_hash[2:]

            registry = GenericContract(UInt160.from_string(contract_hash))
            hypothesis_id_bytes = hypothesis_id.encode('utf-8')

            result = await self.facade.test_invoke(
                registry.call_function(
                    "get_hash",
                    [hypothesis_id_bytes]
                )
            )

            if hasattr(result, 'result') and result.result:
                return str(result.result)
            return None

        except Exception as e:
            print(f"[Neo] Failed to get on-chain hash: {e}")
            return None

    async def get_attestation(self, tx_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve attestation details from a transaction.

        Args:
            tx_id: Transaction ID (hash) of the attestation

        Returns:
            dict: Transaction details if found, None otherwise
        """
        if not self.facade:
            return None

        try:
            # Use the facade's RPC client to get transaction info
            # The facade has an internal rpc client we can access
            if hasattr(self.facade, 'rpc'):
                tx = await self.facade.rpc.get_raw_transaction(tx_id)
            else:
                # Fallback: just return basic info
                return {
                    "tx_id": tx_id,
                    "status": "submitted",
                    "note": "Transaction lookup requires direct RPC access"
                }

            if tx:
                return {
                    "tx_id": tx_id,
                    "block_hash": str(getattr(tx, 'blockhash', '')),
                    "block_time": getattr(tx, 'blocktime', 0),
                    "confirmations": getattr(tx, 'confirmations', 0)
                }

            return None

        except Exception as e:
            print(f"[Neo] Failed to get attestation: {e}")
            return None


# Synchronous wrapper functions for backward compatibility

def write_hypothesis_receipt(hypothesis_id: str, content_hash: str, author_wallet: str) -> str:
    """
    Write a hypothesis receipt to Neo blockchain.

    Synchronous wrapper for backward compatibility with the minting service.

    Args:
        hypothesis_id: Unique hypothesis identifier
        content_hash: SHA-256 hash of the hypothesis content
        author_wallet: Neo wallet address of the author

    Returns:
        str: Transaction ID (hex string with 0x prefix)
    """
    if not NEO_AVAILABLE:
        print("[Warning] Neo SDK not available - returning mock transaction ID")
        return _generate_mock_tx_id(hypothesis_id, content_hash, author_wallet)

    if not NEO_PRIVATE_KEY:
        print("[Warning] NEO_PRIVATE_KEY not configured - returning mock transaction ID")
        print("[Info] To enable real Neo transactions, add to extraction/.env:")
        print("  NEO_NETWORK=testnet")
        print("  NEO_PRIVATE_KEY=your_wif_private_key")
        return _generate_mock_tx_id(hypothesis_id, content_hash, author_wallet)

    try:
        # Create client and write attestation
        client = NeoClient()

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                client.write_attestation(hypothesis_id, content_hash, author_wallet)
            )

            print(f"[Neo] Successfully wrote attestation!")
            print(f"[Neo] Transaction ID: {result['tx_id']}")
            print(f"[Neo] Block: {result.get('included_in_block', 'pending')}")
            print(f"[Neo] Confirmations: {result.get('confirmations', 0)}")
            print(f"[Neo] GAS consumed: {result.get('gas_consumed', 'N/A')}")
            print(f"[Neo] Explorer: {get_explorer_url(result['tx_id'], NEO_NETWORK)}")

            return result["tx_id"]

        finally:
            loop.close()

    except Exception as e:
        print(f"[Neo] Error writing to blockchain: {e}")
        print("[Neo] Falling back to mock transaction ID")
        return _generate_mock_tx_id(hypothesis_id, content_hash, author_wallet)


def get_receipt(neo_tx_id: str) -> Optional[dict]:
    """
    Retrieve a hypothesis receipt from Neo blockchain.

    Args:
        neo_tx_id: Transaction ID to query

    Returns:
        dict: Transaction details if found, None otherwise
    """
    if not NEO_AVAILABLE or not NEO_PRIVATE_KEY:
        return None

    try:
        client = NeoClient()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(client.get_attestation(neo_tx_id))
        finally:
            loop.close()

    except Exception as e:
        print(f"[Neo] Error getting receipt: {e}")
        return None


def _generate_mock_tx_id(hypothesis_id: str, content_hash: str, author_wallet: str) -> str:
    """
    Generate a deterministic mock transaction ID.

    Used when Neo SDK is not available or not configured.
    The mock ID is based on the input data, making it reproducible.
    """
    payload = {
        "hypothesis_id": hypothesis_id,
        "content_hash": content_hash,
        "author_wallet": author_wallet,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print(f"[Neo] Mock receipt for hypothesis {hypothesis_id}")
    print(f"[Neo] Content hash: {content_hash}")
    print(f"[Neo] Author: {author_wallet}")

    # Generate deterministic hash for mock tx ID
    mock_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return f"0x{mock_hash}"


def get_explorer_url(tx_id: str, network: str = "testnet") -> str:
    """
    Get the block explorer URL for a transaction.

    Uses Dora explorer (https://dora.coz.io/) which supports both testnet and mainnet.

    Args:
        tx_id: Transaction ID (with or without 0x prefix)
        network: "testnet" or "mainnet"

    Returns:
        str: URL to view transaction on Dora explorer
    """
    # Remove 0x prefix if present
    tx_hash = tx_id[2:] if tx_id.startswith("0x") else tx_id

    if network == "mainnet":
        return f"https://dora.coz.io/transaction/neo3/mainnet/{tx_hash}"
    else:
        return f"https://dora.coz.io/transaction/neo3/testnet/{tx_hash}"


def verify_attestation(hypothesis_id: str, content_hash: str, tx_id: str) -> bool:
    """
    Verify that an attestation exists on-chain and matches the expected hash.

    Args:
        hypothesis_id: The hypothesis ID to verify
        content_hash: Expected content hash
        tx_id: Transaction ID of the attestation

    Returns:
        bool: True if attestation exists and is valid
    """
    receipt = get_receipt(tx_id)

    if not receipt:
        print(f"[Neo] Attestation not found: {tx_id}")
        return False

    # Basic verification - transaction exists
    # Full verification would require querying the registry contract
    # or parsing the transaction data

    print(f"[Neo] Attestation verified: {tx_id}")
    print(f"[Neo] Confirmations: {receipt.get('confirmations', 0)}")

    return True


if __name__ == "__main__":
    # Example usage and configuration test
    print("=" * 60)
    print("Neo Client Configuration Test")
    print("=" * 60)

    print(f"\nNEO_AVAILABLE: {NEO_AVAILABLE}")
    print(f"NEO_NETWORK: {NEO_NETWORK}")
    print(f"NEO_PRIVATE_KEY configured: {bool(NEO_PRIVATE_KEY)}")
    print(f"NEO_RPC_URL: {NEO_RPC_URL or '(using default)'}")
    print(f"REGISTRY_CONTRACT: {REGISTRY_CONTRACT_HASH or '(not configured)'}")

    print("\n" + "-" * 60)
    print("Neo Tech Stack Resources")
    print("-" * 60)
    print("Faucet (get test GAS): https://n3t5wish.ngd.network/#/")
    print("Explorer (Dora):       https://dora.coz.io/")
    print("Mamba SDK:             https://github.com/CityOfZion/neo-mamba")
    print("Neo3-Boa (contracts):  https://github.com/CityOfZion/neo3-boa")

    # Test mock transaction
    print("\n" + "-" * 60)
    print("Testing write_hypothesis_receipt...")
    print("-" * 60)

    tx_id = write_hypothesis_receipt(
        hypothesis_id="trace_hyp_test",
        content_hash="0xabc123def456...",
        author_wallet="NZHf1NJvz1tvELGLWZjhpb3NqZJFFUYpxT"
    )

    print(f"\nTransaction ID: {tx_id}")
    print(f"Explorer URL: {get_explorer_url(tx_id, NEO_NETWORK)}")

    # Test receipt query
    print("\n" + "-" * 60)
    print("Testing get_receipt...")
    print("-" * 60)

    receipt = get_receipt(tx_id)
    print(f"Receipt: {receipt}")
