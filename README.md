# Trace: Scientific Hypothesis Generation Pipeline

**Trace** is an AI-powered pipeline that processes two research paper PDFs and generates testable scientific hypotheses by identifying synergies and combining insights from both papers.

## Overview

Trace uses Large Language Models (LLMs) to extract structured information from research papers, analyzes synergies and conflicts between them using graph-based reasoning, and generates falsifiable scientific hypotheses. The system integrates with Neo blockchain for verification and NeoFS for decentralized storage.

## Features

- **5-Phase Pipeline:** PDF reading → Extraction → Synergy Analysis → Hypothesis Generation → Minting
- **SpoonOS Integration:** Uses SpoonOS Agent protocol and Tools throughout
- **Workflow Orchestration:** Spoon StateGraph for reliable pipeline execution
- **Graph-Based Reasoning:** Identifies synergies and conflicts using knowledge graphs
- **Semantic Validation:** Prevents hallucinations by validating all claim references
- **Blockchain Verification:** Neo blockchain attestation with content hashing
- **Decentralized Storage:** NeoFS integration for hypothesis storage
- **Micropayment Support:** X402 payment protocol integration

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Groq API key
- (Optional) Neo wallet for blockchain integration
- (Optional) NeoFS configuration for decentralized storage
- (Optional) X402 configuration for micropayments

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Trace
```

2. Ensure Python 3.12+ is installed:
```bash
python3 --version  # Should show Python 3.12.x or higher
```

   If Python 3.12+ is not installed, install it using:
   - **macOS:** `brew install python@3.12` or download from [python.org](https://www.python.org/downloads/)
   - **Linux:** Use your distribution's package manager (e.g., `sudo apt install python3.12`)
   - **Windows:** Download from [python.org](https://www.python.org/downloads/)

3. Create and activate a virtual environment (recommended):
```bash
# Create virtual environment with Python 3.12
python3.12 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
# Create extraction/.env file
GROQ_API_KEY=your_groq_api_key_here

# Optional: Neo blockchain
NEO_NETWORK=testnet
NEO_PRIVATE_KEY=your_wif_private_key

# Optional: NeoFS storage
NEOFS_ENDPOINT=grpc://st1.storage.fs.neo.org:8080
NEOFS_OWNER_ADDRESS=NXxxxxYourNeoAddressHere
NEOFS_PRIVATE_KEY_WIF=your_wif_private_key

# Optional: X402 payment
X402_PRIVATE_KEY=0x...your_eth_private_key
X402_RECEIVER_ADDRESS=0x...
X402_NETWORK=base-sepolia
X402_MINT_FEE=0.001
```

5. Place 2 PDF files in `input_pdfs/` folder

6. Run the pipeline:
```bash
python process_papers.py --author-wallet NYourWalletAddress
```

## How It Works

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: 2 PDF Files                        │
│                  (input_pdfs/ folder)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 0: PDF Reading                            │
│  • Extract title + abstract from each PDF                   │
│  • Limit to ~3000-5000 characters                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         PHASE 1: Structured Extraction                      │
│  • Extract claims, methods, evidence, limitations, vars   │
│  • Uses SpoonOS Tool → SpoonOS → Groq LLM                   │
│  • Output: Paper A JSON + Paper B JSON (parallel)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         PHASE 2: Synergy Analysis                           │
│  • Build graph (claims, variables, relationships)          │
│  • Identify overlapping variables                         │
│  • Find synergies and conflicts                            │
│  • Uses SpoonOS Agent (SpoonReactAI)                        │
│  • Output: Synergy JSON with graph structure               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         PHASE 3: Hypothesis Generation                      │
│  • Select primary synergy                                │
│  • Generate testable "if-then" hypothesis                  │
│  • Semantic validation (anti-hallucination)               │
│  • Retry logic (up to 2 retries)                          │
│  • Uses SpoonOS Agent (SpoonReactAI)                        │
│  • Output: Hypothesis Card JSON                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         PHASE 4: Hypothesis Minting                         │
│  • Validate hypothesis card                                │
│  • Canonicalise JSON (deterministic)                        │
│  • Compute SHA-256 content hash                            │
│  • Save to off-chain registry                              │
│  • Write Neo blockchain receipt                             │
│  • Store on NeoFS (SpoonOS Tool)                           │
│  • Process X402 payment (SpoonOS Tool, optional)           │
│  • Output: Mint Result + Saved Files                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT: Complete Results                  │
│  • Paper A JSON                                            │
│  • Paper B JSON                                            │
│  • Synergy Analysis JSON                                   │
│  • Hypothesis Card JSON                                    │
│  • Mint Result (hash, tx IDs, etc.)                        │
│  • Saved files in data/hypotheses/                         │
└─────────────────────────────────────────────────────────────┘
```

### Phase Details

#### Phase 0: PDF Reading
- Extracts title and abstract from each PDF
- Uses PyPDF2 for PDF parsing
- Limits text to ~3000-5000 characters to reduce token usage

#### Phase 1: Structured Extraction
- Uses SpoonOS Tool to extract structured information
- Extracts: claims, methods, evidence (1-2 items), limitations, variables
- Runs in parallel for both papers
- Uses Groq LLM (llama-3.3-70b-versatile) via SpoonOS

#### Phase 2: Synergy Analysis
- Builds knowledge graph from Phase 1 outputs
- Uses SpoonOS Agent to identify:
  - Overlapping variables (semantic matching)
  - Potential synergies (complementary findings)
  - Potential conflicts (contradictions)
- Enhances graph with analysis results

#### Phase 3: Hypothesis Generation
- Selects primary synergy based on scoring
- Generates testable "if-then" hypothesis
- Validates semantic grounding (all claim IDs must exist)
- Retry logic: up to 2 retries if validation fails
- Auto-fixes invalid references or marks low confidence

#### Phase 4: Hypothesis Minting
- Validates hypothesis card structure
- Creates deterministic JSON (canonical form)
- Computes SHA-256 content hash
- Saves to off-chain registry (`data/hypotheses/`)
- Writes Neo blockchain receipt (on-chain attestation)
- Stores on NeoFS using SpoonOS Tools (decentralized storage)
- Processes X402 payment using SpoonOS Tools (micropayment)

### Workflow Orchestration

The pipeline uses **Spoon StateGraph** for workflow orchestration:

- **Nodes:** Each phase is a node in the workflow graph
- **State:** `PipelineState` TypedDict flows through all nodes
- **Parallel Execution:** Phase 1 runs both extractions in parallel
- **Error Handling:** Nodes set error state on failure, subsequent nodes skip
- **Fallback:** If StateGraph unavailable, falls back to sequential processing

## Usage

### Command Line

```bash
# Basic usage (defaults)
python process_papers.py

# Specify input folder
python process_papers.py --input-folder /path/to/pdfs

# Specify author wallet
python process_papers.py --author-wallet NYourNeoWalletAddress

# Disable NeoFS
python process_papers.py --no-neofs

# Enable X402 payment
python process_papers.py --use-x402

# All options
python process_papers.py \
  --input-folder input_pdfs \
  --author-wallet NYourWallet \
  --use-neofs \
  --use-x402
```

### Python API

```python
import asyncio
from process_papers import process_papers_from_folder

# Process 2 PDFs from default folder
result = asyncio.run(process_papers_from_folder(
    input_folder="input_pdfs",
    author_wallet="NYourWalletAddress",
    use_neofs=True,
    use_x402=False
))

# Access results
if "error" not in result:
    paper_a = result["paper_a"]
    paper_b = result["paper_b"]
    synergy_analysis = result["synergy_analysis"]
    hypothesis = result["hypothesis"]
    mint_result = result["mint_result"]
    
    print(f"Hypothesis ID: {mint_result['hypothesis_id']}")
    print(f"Content Hash: {mint_result['content_hash']}")
    print(f"Neo TX ID: {mint_result['neo_tx_id']}")
```

## Output Structure

### Hypothesis Card

Each generated hypothesis is saved as a JSON file in `data/hypotheses/`:

```json
{
  "hypothesis_id": "trace_hyp_d5a1e2e3",
  "primary_synergy_id": "syn_1",
  "hypothesis": "If blockchain-based approaches from Paper A are applied to Agentic AI systems from Paper B, then the reproducibility of scientific research will increase.",
  "rationale": "Explanation referencing claim IDs...",
  "source_support": {
    "paper_A_claim_ids": ["A_claim_1", "A_claim_3"],
    "paper_B_claim_ids": ["B_claim_1", "B_claim_4"],
    "variables_used": ["temperature", "state_of_health"]
  },
  "proposed_experiment": {
    "description": "Experimental setup...",
    "measurements": ["measurement1", "measurement2"],
    "expected_direction": "increase"
  },
  "confidence": "medium",
  "risk_notes": ["Assumption 1", "Assumption 2"],
  "content_hash": "0xb77781389cc4beeafcc1732be749635921e96d3b900b23590d9c1f39e3df4c01",
  "created_at": "2025-12-07T01:22:28.524999+00:00",
  "version": "v1",
  "author_wallet": "NYourWalletAddress",
  "neo_tx_id": "0xc436a739627d8941a460bbc3314506fff5387ceb621eeadc5e891e66318efac8",
  "neofs_object_id": "object_id_from_neofs",
  "neofs_container_id": "container_id_from_neofs"
}
```

### Mint Result

The mint result contains all transaction IDs and metadata:

```json
{
  "hypothesis_id": "trace_hyp_d5a1e2e3",
  "content_hash": "0xb77781389cc4beeafcc1732be749635921e96d3b900b23590d9c1f39e3df4c01",
  "neo_tx_id": "0xc436a739627d8941a460bbc3314506fff5387ceb621eeadc5e891e66318efac8",
  "created_at": "2025-12-07T01:22:28.524999+00:00",
  "version": "v1",
  "neofs": {
    "object_id": "object_id_from_neofs",
    "container_id": "container_id_from_neofs",
    "success": true
  },
  "x402": {
    "tx_hash": "0x...",
    "amount_usdc": 0.001,
    "network": "base-sepolia",
    "success": true
  }
}
```

## NeoFS Integration

Trace uses **SpoonOS NeoFS Tools** for decentralized storage:

- **CreateContainerTool:** Creates storage containers on NeoFS
- **UploadObjectTool:** Uploads hypothesis cards to NeoFS
- **DownloadObjectByIdTool:** Retrieves stored hypotheses
- **SearchObjectsTool:** Searches hypotheses by attributes

### NeoFS Configuration

```bash
NEOFS_ENDPOINT=grpc://st1.storage.fs.neo.org:8080
NEOFS_OWNER_ADDRESS=NXxxxxYourNeoAddressHere
NEOFS_PRIVATE_KEY_WIF=your_wif_private_key
NEOFS_CONTAINER_ID=optional_existing_container_id
```

When enabled, hypotheses are automatically stored on NeoFS with searchable attributes (HypothesisId, ContentHash, Type, etc.).

## X402 Payment Integration

Trace uses **SpoonOS X402 Tools** for micropayment processing:

- **X402PaymentHeaderTool:** Generates payment headers
- **X402PaywalledRequestTool:** Processes paywalled requests

### X402 Configuration

```bash
X402_PRIVATE_KEY=0x...your_eth_private_key
X402_RECEIVER_ADDRESS=0x...
X402_NETWORK=base-sepolia
X402_MINT_FEE=0.001
```

When enabled, each hypothesis minting triggers an X402 micropayment (default: 0.001 USDC on base-sepolia network).

## Neo Blockchain Integration

Trace writes hypothesis receipts to the Neo blockchain:

- **Content Hash:** SHA-256 hash of canonical hypothesis JSON
- **Transaction ID:** Neo transaction ID for on-chain attestation
- **Author Wallet:** Wallet address of hypothesis author

### Neo Configuration

```bash
NEO_NETWORK=testnet
NEO_PRIVATE_KEY=your_wif_private_key
NEO_RPC_URL=custom_rpc_url
NEO_REGISTRY_CONTRACT=contract_hash
```

The system uses `neo-mamba` SDK for blockchain interactions. If unavailable, it falls back to mock transaction IDs.

## SpoonOS Integration

Trace extensively uses SpoonOS throughout:

### Phase 1: SpoonOS Tool
- Tool: `extract_paper_structure`
- Function: Extracts structured information from paper text
- Flow: Tool → SpoonOS ChatBot → Groq LLM

### Phase 2 & 3: SpoonOS Agent
- Agent: `SpoonReactAI`
- Function: Analyzes synergies and generates hypotheses
- Flow: Agent → SpoonOS ChatBot → Groq LLM

### Phase 4: SpoonOS Tools
- NeoFS Tools: `CreateContainerTool`, `UploadObjectTool`, etc.
- X402 Tools: `X402PaymentHeaderTool`, `X402PaywalledRequestTool`

## Error Handling

The pipeline includes comprehensive error handling:

- **Phase 0:** Validates PDF files exist and are readable
- **Phase 1:** Auto-repairs malformed JSON from LLM
- **Phase 2:** Validates input structure, handles LLM failures
- **Phase 3:** Retry logic (up to 2 retries) with semantic validation
- **Phase 4:** Graceful degradation if NeoFS/X402 unavailable

All errors are logged and included in the result dictionary.

## Performance

### Typical Execution Times

- **PDF Reading:** ~1 second
- **Phase 1:** ~3-6 seconds (2 LLM calls, parallel)
- **Phase 2:** ~3-5 seconds (1 LLM call)
- **Phase 3:** ~3-5 seconds (1 LLM call, may retry)
- **Phase 4:** ~1-2 seconds (local + optional NeoFS/X402)

**Total:** ~10-18 seconds for complete pipeline

### Token Usage

- **Phase 1:** ~2000-4000 tokens per paper
- **Phase 2:** ~3000-5000 tokens
- **Phase 3:** ~3000-5000 tokens

**Total:** ~11,000-19,000 tokens per pipeline run

## Project Structure

```
Trace/
├── extraction/          # Phase 0 & 1
│   ├── pdf_reader.py     # PDF text extraction
│   ├── spoon_tool.py     # SpoonOS Tool for extraction
│   └── extract_paper.py  # Core LLM extraction logic
├── phase2/              # Phase 2
│   └── synergy_agent.py # SpoonOS Agent for synergy analysis
├── phase3/              # Phase 3
│   └── hypothesis_agent.py # SpoonOS Agent for hypothesis generation
├── phase4/              # Phase 4
│   ├── minting_service.py # Core minting logic
│   ├── registry_store.py  # Off-chain registry
│   ├── neo_client.py      # Neo blockchain integration
│   └── spoon_tools.py     # NeoFS & X402 SpoonOS Tools
├── pipeline_workflow.py  # Spoon StateGraph workflow
├── process_papers.py     # Main entry point
├── input_pdfs/          # Input PDF files (2 required)
├── data/
│   └── hypotheses/       # Generated hypothesis cards
└── web/                 # Web frontend/website
    └── README.md         # Web folder documentation
```

## Requirements

### Required

- `groq` - LLM API client
- `python-dotenv` - Environment variable management
- `PyPDF2>=3.0` - PDF text extraction
- `spoon-ai-sdk` - SpoonOS integration

### Optional

- `neo-mamba` - Neo blockchain SDK (for real on-chain attestations)
- NeoFS SDK (included in spoon-ai-sdk if available)
- X402 SDK (included in spoon-ai-sdk if available)

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure all tests pass and follow the existing code style.

## Support

For issues and questions, please open an issue on the repository.

---

**Trace** - Generating testable scientific hypotheses from research papers.

