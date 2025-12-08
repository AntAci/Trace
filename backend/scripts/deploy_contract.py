"""
Deploy Hypothesis Registry Contract to Neo N3

This script deploys the compiled hypothesis_registry contract to Neo N3 testnet/mainnet.

Prerequisites:
1. Compile the contract first: neo3-boa compile contracts/hypothesis_registry.py
2. Have a funded Neo wallet configured in extraction/.env
3. Have neo-mamba installed: pip install neo-mamba

Usage:
    python scripts/deploy_contract.py
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
env_path = Path(__file__).parent.parent / "extraction" / ".env"
load_dotenv(env_path)

# Try to import neo-mamba SDK
try:
    from neo3.api.wrappers import ChainFacade
    from neo3.api.helpers.signing import sign_with_account
    from neo3.network.payloads.verification import Signer
    from neo3.wallet.account import Account
    from neo3.contracts.nef import NEF
    from neo3.contracts.manifest import ContractManifest
    from neo3.core.types import UInt160
    NEO_AVAILABLE = True
except ImportError as e:
    NEO_AVAILABLE = False
    print(f"[Error] neo-mamba SDK not available: {e}")
    print("Install with: pip install neo-mamba")
    sys.exit(1)

# Configuration
NEO_NETWORK = os.getenv("NEO_NETWORK", "testnet")
NEO_PRIVATE_KEY = os.getenv("NEO_PRIVATE_KEY", "")

# Contract files
CONTRACT_DIR = Path(__file__).parent.parent / "contracts"
NEF_FILE = CONTRACT_DIR / "hypothesis_registry.nef"
MANIFEST_FILE = CONTRACT_DIR / "hypothesis_registry.manifest.json"

# ContractManagement native contract hash (same on all Neo N3 networks)
CONTRACT_MANAGEMENT_HASH = "0xfffdc93764dbaddd97c48f252a53ea4643faa3fd"


async def deploy_contract():
    """Deploy the hypothesis registry contract to Neo N3."""

    print("=" * 60)
    print("Hypothesis Registry Contract Deployment")
    print("=" * 60)

    # Check prerequisites
    if not NEO_PRIVATE_KEY:
        print("\n[Error] NEO_PRIVATE_KEY not configured in extraction/.env")
        print("Run: python scripts/create_wallet.py")
        return None

    if not NEF_FILE.exists():
        print(f"\n[Error] NEF file not found: {NEF_FILE}")
        print("Compile first: neo3-boa compile contracts/hypothesis_registry.py")
        return None

    if not MANIFEST_FILE.exists():
        print(f"\n[Error] Manifest file not found: {MANIFEST_FILE}")
        print("Compile first: neo3-boa compile contracts/hypothesis_registry.py")
        return None

    print(f"\nNetwork: {NEO_NETWORK}")
    print(f"NEF file: {NEF_FILE}")
    print(f"Manifest: {MANIFEST_FILE}")

    # Load account
    account = Account.from_wif(NEO_PRIVATE_KEY)
    print(f"Deployer: {account.address}")

    # Create facade
    if NEO_NETWORK == "mainnet":
        facade = ChainFacade.node_provider_mainnet()
    else:
        facade = ChainFacade.node_provider_testnet()

    # Configure signer
    facade.add_signer(
        sign_with_account(account),
        Signer(account.script_hash)
    )

    # Load NEF and manifest
    print("\nLoading contract files...")

    with open(NEF_FILE, 'rb') as f:
        nef_bytes = f.read()

    with open(MANIFEST_FILE, 'r') as f:
        manifest_dict = json.load(f)
    manifest_json = json.dumps(manifest_dict)

    print(f"NEF size: {len(nef_bytes)} bytes")
    print(f"Manifest size: {len(manifest_json)} bytes")

    # Deploy using ContractManagement.deploy
    print("\nDeploying contract...")
    print("(This may take 15-30 seconds)")

    try:
        from neo3.api.wrappers import GenericContract

        # ContractManagement native contract
        contract_management = GenericContract(UInt160.from_string(CONTRACT_MANAGEMENT_HASH[2:]))

        # Call deploy method
        # deploy(nefFile: ByteString, manifest: String, data: Any) -> Contract
        receipt = await facade.invoke(
            contract_management.call_function(
                "deploy",
                [nef_bytes, manifest_json, None]
            )
        )

        print("\n" + "=" * 60)
        print("DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        print(f"\nTransaction ID: {receipt.tx_hash}")
        print(f"Block: {receipt.included_in_block}")
        print(f"GAS consumed: {receipt.gas_consumed}")

        # Calculate contract hash
        # Contract hash = Hash160(sender + nef_checksum + contract_name)
        # For now, we'll need to look it up in the transaction result or explorer

        print(f"\n[Info] Find your contract hash on the explorer:")
        print(f"https://dora.coz.io/transaction/neo3/{NEO_NETWORK}/{receipt.tx_hash}")

        return str(receipt.tx_hash)

    except Exception as e:
        print(f"\n[Error] Deployment failed: {e}")
        return None


def main():
    """Main entry point."""
    if not NEO_AVAILABLE:
        print("neo-mamba SDK required for deployment")
        sys.exit(1)

    tx_hash = asyncio.run(deploy_contract())

    if tx_hash:
        print("\n" + "-" * 60)
        print("NEXT STEPS:")
        print("-" * 60)
        print("""
1. Wait for transaction confirmation (~15 seconds)

2. Find your contract hash on the explorer:
   - Search for your transaction ID
   - Look for the deployed contract address

3. Add the contract hash to your .env file:
   NEO_REGISTRY_CONTRACT=0x<your_contract_hash>

4. The neo_client.py will automatically use the registry
   contract for hypothesis attestations!
""")
    else:
        print("\nDeployment failed. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
