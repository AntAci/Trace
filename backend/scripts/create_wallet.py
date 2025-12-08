"""
Neo N3 Wallet Generator for Trace Project

This script creates a new Neo N3 wallet for testing blockchain transactions.

IMPORTANT:
- Save your private key (WIF) securely - it cannot be recovered!
- Never share your private key
- This wallet is for TESTNET use only
"""
import sys

try:
    from neo3.wallet.account import Account
    NEO_AVAILABLE = True
except ImportError:
    NEO_AVAILABLE = False
    print("=" * 60)
    print("ERROR: neo-mamba SDK not installed")
    print("=" * 60)
    print("\nPlease install it first:")
    print("  pip install neo-mamba")
    print()
    sys.exit(1)


def create_wallet():
    """Create a new Neo N3 wallet and display credentials."""
    print("=" * 60)
    print("Neo N3 Wallet Generator")
    print("=" * 60)

    # Generate new account
    account = Account.create_new()

    print("\n✅ NEW WALLET CREATED SUCCESSFULLY!\n")
    print("-" * 60)
    print("SAVE THESE CREDENTIALS SECURELY:")
    print("-" * 60)

    # Get WIF from private key
    wif = Account.private_key_to_wif(account.private_key)

    print(f"\n📍 Address (public):     {account.address}")
    print(f"🔑 Private Key (WIF):    {wif}")
    print(f"📋 Script Hash:          {account.script_hash}")

    print("\n" + "-" * 60)
    print("NEXT STEPS:")
    print("-" * 60)
    print("""
1. COPY your WIF private key above (starts with 'K' or 'L')

2. GET TESTNET GAS:
   Go to: https://n3t5wish.ngd.network/#/
   Paste your ADDRESS (starts with 'N') to receive free testnet GAS

3. ADD TO YOUR .env FILE:
   Edit: Trace/extraction/.env
   Add these lines:
""")

    print(f"   NEO_NETWORK=testnet")
    print(f"   NEO_PRIVATE_KEY={wif}")

    print("""
4. VERIFY ON EXPLORER:
   After getting GAS, check your balance at:
   https://dora.coz.io/
   Search for your address to see your balance

5. RUN THE PIPELINE:
   python process_papers.py

   Your hypothesis will now be minted to the REAL Neo N3 testnet!
""")

    print("=" * 60)
    print("⚠️  SECURITY WARNING")
    print("=" * 60)
    print("""
- NEVER share your private key (WIF)
- NEVER commit your .env file to git
- This is a TESTNET wallet - don't use for real funds
- Keep a backup of your WIF in a secure location
""")

    return account


def check_existing_config():
    """Check if there's already a private key configured."""
    import os
    from pathlib import Path
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / "extraction" / ".env"
    load_dotenv(env_path)

    existing_key = os.getenv("NEO_PRIVATE_KEY", "")

    if existing_key:
        print("=" * 60)
        print("EXISTING CONFIGURATION FOUND")
        print("=" * 60)
        print(f"\nYou already have a private key configured in:")
        print(f"  {env_path}")
        print("\nDo you want to create a NEW wallet anyway?")
        print("(This will NOT overwrite your existing config)")

        response = input("\nCreate new wallet? [y/N]: ").strip().lower()
        if response != 'y':
            print("\nExiting. Your existing configuration is unchanged.")
            sys.exit(0)


if __name__ == "__main__":
    check_existing_config()
    account = create_wallet()
