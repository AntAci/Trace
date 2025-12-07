# Trace: Complete Technical Documentation

**Version:** 1.0  
**Last Updated:** 2025-12-07  
**System:** Scientific Hypothesis Generation Pipeline

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Complete Pipeline Flow](#complete-pipeline-flow)
4. [Phase 0: PDF Reading](#phase-0-pdf-reading)
5. [Phase 1: Structured Extraction](#phase-1-structured-extraction)
6. [Phase 2: Synergy Analysis](#phase-2-synergy-analysis)
7. [Phase 3: Hypothesis Generation](#phase-3-hypothesis-generation)
8. [Phase 4: Hypothesis Minting](#phase-4-hypothesis-minting)
9. [Workflow Orchestration](#workflow-orchestration)
10. [Data Structures](#data-structures)
11. [SpoonOS Integration](#spoonos-integration)
12. [Error Handling](#error-handling)
13. [Configuration](#configuration)

---

## System Overview

**Trace** is a 5-phase scientific hypothesis generation pipeline that processes two research paper PDFs and generates testable scientific hypotheses. The system uses LLM-based extraction, graph-based reasoning, and blockchain verification.

### Key Technologies

- **LLM Provider:** Groq (llama-3.3-70b-versatile) via SpoonOS
- **PDF Processing:** PyPDF2
- **Workflow Orchestration:** Spoon StateGraph (spoon-ai-sdk)
- **Graph Analysis:** In-memory dict-based graphs + optional Spoon Graph
- **Blockchain:** Neo N3 (via neo-mamba SDK)
- **Storage:** File-based JSON registry + NeoFS (SpoonOS Tool)
- **Payment:** X402 micropayment protocol (SpoonOS Tool)

### Architecture Principles

- **Modular Design:** Each phase is independent and consumes only previous phase outputs
- **SpoonOS Integration:** Uses SpoonOS Agent protocol (Phase 2, 3) and Tools (Phase 1, 4)
- **Workflow Graph:** Spoon StateGraph orchestrates the entire pipeline
- **Deterministic Hashing:** SHA-256 content hashing for verification
- **Dual Storage:** Off-chain registry for full data, on-chain for proof
- **Graceful Degradation:** System works even if optional components are unavailable

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Spoon StateGraph Workflow                 │
│              (pipeline_workflow.py)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                      │
        ▼                                      ▼
┌───────────────┐                      ┌───────────────┐
│  Phase 0      │                      │  Phase 1      │
│  PDF Reading  │                      │  Extraction   │
│               │                      │  (Parallel)   │
└───────┬───────┘                      └───────┬───────┘
        │                                      │
        └──────────────┬───────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Phase 2        │
              │  Synergy        │
              │  Analysis       │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Phase 3        │
              │  Hypothesis     │
              │  Generation      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Phase 4        │
              │  Minting        │
              │  (Registry +    │
              │   Neo + NeoFS + │
              │   X402)         │
              └─────────────────┘
```

### Component Structure

```
Trace/
├── extraction/          # Phase 0 & 1
│   ├── pdf_reader.py     # PDF text extraction
│   ├── spoon_tool.py     # SpoonOS Tool for extraction
│   └── extract_paper.py # Core LLM extraction logic
├── phase2/               # Phase 2
│   └── synergy_agent.py  # SpoonOS Agent for synergy analysis
├── phase3/               # Phase 3
│   └── hypothesis_agent.py # SpoonOS Agent for hypothesis generation
├── phase4/               # Phase 4
│   ├── minting_service.py # Core minting logic
│   ├── registry_store.py  # Off-chain registry
│   ├── neo_client.py      # Neo blockchain integration
│   └── spoon_tools.py     # NeoFS & X402 SpoonOS Tools
├── pipeline_workflow.py   # Spoon StateGraph workflow
└── process_papers.py      # Main entry point
```

---

## Complete Pipeline Flow

### Workflow Graph Structure

The pipeline uses Spoon StateGraph with the following nodes:

1. **read_pdfs** (Phase 0) → Entry point
2. **extract_paper_a** (Phase 1a) → Parallel
3. **extract_paper_b** (Phase 1b) → Parallel
4. **analyze_synergy** (Phase 2) → Sequential
5. **generate_hypothesis** (Phase 3) → Sequential
6. **mint_hypothesis** (Phase 4) → Sequential → End

### State Flow

The `PipelineState` TypedDict flows through all nodes:

```python
class PipelineState(TypedDict, total=False):
    # Input
    input_folder: str
    author_wallet: str
    use_neofs: bool
    use_x402: bool
    
    # Phase 0 outputs
    paper_a_text: str
    paper_b_text: str
    paper_a_title: Optional[str]
    paper_b_title: Optional[str]
    
    # Phase 1 outputs
    paper_a_json: Dict[str, Any]
    paper_b_json: Dict[str, Any]
    
    # Phase 2 outputs
    synergy_json: Dict[str, Any]
    
    # Phase 3 outputs
    hypothesis_card: Dict[str, Any]
    
    # Phase 4 outputs
    mint_result: Dict[str, Any]
    
    # Error handling
    error: Optional[str]
    error_phase: Optional[str]
    
    # Metadata
    pipeline_started_at: str
    pipeline_completed_at: Optional[str]
```

---

## Phase 0: PDF Reading

### Purpose

Extract text from PDF files, focusing on title and abstract to reduce token usage.

### Implementation

**File:** `extraction/pdf_reader.py`

**Main Function:** `read_pdfs_from_folder(folder_path: str) -> Tuple[str, str, Optional[str], Optional[str]]`

### Technical Details

1. **PDF Discovery:**
   - Scans folder for exactly 2 PDF files
   - Validates file count (raises `ValueError` if not exactly 2)
   - Sorts files alphabetically for consistent ordering

2. **Text Extraction:**
   - Uses PyPDF2 `PdfReader` to read PDFs
   - Extracts text from first 2 pages only
   - Calls `_extract_abstract_section()` to find abstract
   - Calls `extract_title_from_pdf()` to get title

3. **Abstract Extraction Algorithm:**
   ```python
   # Find "Abstract" or "SUMMARY" marker (case-insensitive)
   # Extract text until end markers: "Keywords", "Introduction", "1. Introduction", etc.
   # Limit to 5000 characters max
   ```

4. **Title Extraction:**
   - First tries PDF metadata (`reader.metadata.title`)
   - Falls back to first line of first page
   - Validates title length (10-200 characters)

5. **Output:**
   - `paper_a_text`: Combined title + abstract (string)
   - `paper_b_text`: Combined title + abstract (string)
   - `paper_a_title`: Extracted title (optional)
   - `paper_b_title`: Extracted title (optional)

### Error Handling

- `FileNotFoundError`: PDF file not found
- `ValueError`: Wrong number of PDFs, empty PDF, or extraction failure

---

## Phase 1: Structured Extraction

### Purpose

Extract structured scientific information from paper text using LLM.

### Implementation

**File:** `extraction/spoon_tool.py` → `extraction/extract_paper.py`

**Main Function:** `extract_paper_structure_async(paper_text: str, title: str = "") -> str`

### Technical Details

1. **SpoonOS Tool Integration:**
   - Implements SpoonOS `Tool` interface
   - Tool name: `extract_paper_structure`
   - Async function: `extract_paper_structure_async()`

2. **LLM Call Flow:**
   ```
   Tool → extract_paper() → SpoonOS ChatBot → Groq LLM
   ```

3. **Prompt Structure:**
   ```
   You are extracting structured scientific information from a research paper.
   
   TITLE: {title}
   PAPER TEXT: {text}
   
   Extract the following fields in STRICT JSON format:
   - claims: list of the main scientific claims (all claims)
   - methods: the main methods or techniques used
   - evidence: concrete evidence supporting the claims (1–2 items)
   - explicit_limitations: limitations directly mentioned
   - implicit_limitations: limitations that follow logically
   - variables: important variables or scientific factors
   
   Return ONLY valid JSON. Do not add commentary.
   ```

4. **JSON Parsing & Repair:**
   - Attempts to parse LLM response as JSON
   - If parsing fails, calls `fix_json_async()` to repair using LLM
   - Validates all required fields exist (defaults to empty arrays if missing)

5. **Evidence Limiting:**
   - Enforces max 2 evidence items (even if LLM returns more)
   - Truncates to first 2 items: `result["evidence"] = result["evidence"][:2]`

6. **Output Schema:**
   ```json
   {
     "claims": ["claim1", "claim2", ...],
     "methods": ["method1", "method2"],
     "evidence": ["evidence1", "evidence2"],  // Max 2
     "explicit_limitations": ["limitation1"],
     "implicit_limitations": ["limitation2"],
     "variables": ["variable1", "variable2"]
   }
   ```

### Parallel Execution

Phase 1 runs **in parallel** for both papers:
- `extract_paper_a_node()` and `extract_paper_b_node()` execute simultaneously
- Workflow graph uses parallel group to ensure both complete before Phase 2

---

## Phase 2: Synergy Analysis

### Purpose

Analyze two papers to identify synergies, conflicts, and overlapping variables using graph-based reasoning.

### Implementation

**File:** `phase2/synergy_agent.py`

**Main Function:** `SynergyAgent.analyze_async(paper_a_json: Dict, paper_b_json: Dict) -> Dict`

### Technical Details

1. **SpoonOS Agent Integration:**
   - Uses `SpoonReactAI` agent (SpoonOS Agent protocol)
   - Agent → SpoonOS ChatBot → Groq LLM
   - Initialized with Groq via OpenAI-compatible API

2. **Graph Building:**
   - Creates in-memory dict-based graph (not Spoon graph objects)
   - **Nodes:**
     - Claims: `{"id": "A_claim_1", "type": "claim", "paper": "A", "text": "..."}`
     - Variables: `{"id": "A_var_1", "type": "variable", "paper": "A", "text": "temperature"}`
   - **Edges:**
     - `uses_variable`: `{"source": "A_claim_1", "target": "A_var_1", "relation": "uses_variable"}`

3. **LLM Analysis:**
   - Builds prompt with both paper JSONs and graph structure
   - Asks LLM to identify:
     - Overlapping variables (semantic matching)
     - Potential synergies (complementary findings)
     - Potential conflicts (contradictions)
   - Parses JSON response (with repair if needed)

4. **Graph Enhancement:**
   - Adds overlapping variable nodes: `{"id": "var_temperature", "type": "variable", "paper": "both", "text": "temperature"}`
   - Adds synergy edges: `{"source": "A_claim_1", "target": "B_claim_1", "relation": "potential_synergy", "synergy_id": "syn_1"}`
   - Adds conflict edges: `{"source": "A_claim_2", "target": "B_claim_2", "relation": "potential_conflict", "conflict_id": "conf_1"}`

5. **Output Schema:**
   ```json
   {
     "overlapping_variables": ["temperature", "state_of_health"],
     "potential_synergies": [
       {
         "id": "syn_1",
         "description": "...",
         "paper_A_support": ["A_claim_1", "A_claim_2"],
         "paper_B_support": ["B_claim_1"]
       }
     ],
     "potential_conflicts": [...],
     "graph": {
       "nodes": [...],
       "edges": [...]
     }
   }
   ```

### Optional Spoon Graph

The system can optionally use Spoon Graph (`GraphTemplate`, `NodeSpec`, `EdgeSpec`) for graph building, but defaults to dict-based representation for the knowledge graph.

---

## Phase 3: Hypothesis Generation

### Purpose

Generate a testable scientific hypothesis from paper synergies with semantic validation and retry logic.

### Implementation

**File:** `phase3/hypothesis_agent.py`

**Main Function:** `HypothesisAgent.generate_hypothesis_async(paper_a_json: Dict, paper_b_json: Dict, synergy_json: Dict) -> Dict`

### Technical Details

1. **SpoonOS Agent Integration:**
   - Uses `SpoonReactAI` agent (same as Phase 2)
   - Agent → SpoonOS ChatBot → Groq LLM

2. **Primary Synergy Selection:**
   - Scores synergies based on:
     - Number of overlapping variables mentioned (+1 each)
     - Number of supporting claims (+1 each)
   - Selects highest-scoring synergy

3. **Hypothesis Generation:**
   - Builds prompt focusing on primary synergy
   - Includes both paper JSONs and graph structure
   - Asks LLM to generate:
     - Testable "if-then" hypothesis
     - Rationale referencing claim IDs
     - Source support (claim IDs and variables)
     - Proposed experiment
     - Confidence level
     - Risk notes

4. **Retry Logic (Up to 2 Retries):**
   ```python
   max_retries = 2
   while retry_count <= max_retries:
       hypothesis_card = await _generate_with_spoonos_async(...)
       validation = _validate_semantic_grounding(...)
       
       if validation["valid"]:
           return hypothesis_card  # Success
       
       if retry_count < max_retries:
           # Retry with feedback
           hypothesis_card = await _generate_with_spoonos_async(..., feedback=validation["errors"])
       else:
           # Max retries reached - fix or mark low confidence
           hypothesis_card = _fix_hypothesis_card(...)
   ```

5. **Semantic Validation (Anti-Hallucination):**
   - Validates all `paper_A_claim_ids` exist in Phase 2 graph
   - Validates all `paper_B_claim_ids` exist in Phase 2 graph
   - Validates all `variables_used` exist in input papers
   - Returns validation result with errors if any

6. **Auto-Fix:**
   - Removes invalid claim IDs from `source_support`
   - Removes invalid variables from `variables_used`
   - Marks as low confidence if significant fixes made

7. **Hypothesis ID Generation:**
   - Format: `trace_hyp_{8_hex_chars}`
   - Generated using `uuid.uuid4().hex[:8]`

8. **Output Schema:**
   ```json
   {
     "hypothesis_id": "trace_hyp_7e88207e",
     "primary_synergy_id": "syn_1",
     "hypothesis": "If X condition from Paper A is applied to Y system from Paper B, then Z effect will occur.",
     "rationale": "Explanation referencing A_claim_1, B_claim_2, etc.",
     "source_support": {
       "paper_A_claim_ids": ["A_claim_1", "A_claim_3"],
       "paper_B_claim_ids": ["B_claim_1", "B_claim_4"],
       "variables_used": ["temperature", "state_of_health"]
     },
     "proposed_experiment": {
       "description": "Experimental setup description",
       "measurements": ["measurement1", "measurement2"],
       "expected_direction": "increase / decrease / non-linear"
     },
     "confidence": "low / medium / high",
     "risk_notes": ["Assumption 1", "Assumption 2"]
   }
   ```

---

## Phase 4: Hypothesis Minting

### Purpose

Mint hypothesis to off-chain registry, Neo blockchain, NeoFS, and X402 with cryptographic verification.

### Implementation

**File:** `phase4/minting_service.py`

**Main Function:** `mint_hypothesis(card: Dict, author_wallet: str, use_neofs: bool = True, use_x402: bool = False) -> Dict`

### Technical Details

1. **Validation:**
   - Validates hypothesis card has all required fields
   - Validates nested structures (`source_support`, `proposed_experiment`)

2. **Canonicalisation:**
   - Creates deterministic JSON representation
   - Extracts only core fields (excludes metadata)
   - Recursively sorts all dictionary keys
   - Returns compact JSON (no extra whitespace)

3. **Content Hash:**
   - Computes SHA-256 hash of canonical JSON
   - Returns hex string prefixed with "0x"
   ```python
   hash_bytes = hashlib.sha256(canonical_json.encode('utf-8')).digest()
   return "0x" + hash_bytes.hex()
   ```

4. **Metadata Enrichment:**
   - Adds `content_hash`, `created_at`, `version`, `author_wallet` to card

5. **Off-Chain Registry:**
   - Saves to `data/hypotheses/{hypothesis_id}.json`
   - Pretty-printed JSON with 2-space indent
   - File-based storage (no database)

6. **Neo Blockchain:**
   - Calls `write_hypothesis_receipt()` from `neo_client.py`
   - Creates NeoClient instance
   - Calls `client.write_attestation()` (async)
   - Returns transaction ID (or mock if SDK unavailable)

7. **NeoFS Storage (SpoonOS Tool):**
   - Uses `NeoFSHypothesisStore` from `spoon_tools.py`
   - Creates/ensures container exists
   - Uploads hypothesis card as JSON object
   - Sets attributes for searchability (HypothesisId, ContentHash, etc.)
   - Returns object ID and container ID

8. **X402 Payment (SpoonOS Tool):**
   - Uses `X402PaymentProcessor` from `spoon_tools.py`
   - Generates payment header using `X402PaymentHeaderTool`
   - Processes payment using `X402PaywalledRequestTool`
   - Returns transaction hash and amount

9. **Registry Update:**
   - Updates saved card with all metadata:
     - `neo_tx_id`
     - `neofs_object_id`, `neofs_container_id`
     - `x402_tx_hash`, `x402_amount_usdc`

10. **Output Schema:**
    ```json
    {
      "hypothesis_id": "trace_hyp_7e88207e",
      "content_hash": "0x78e26a17e1e881ef...",
      "neo_tx_id": "0x0000000000000000...",
      "created_at": "2025-12-06T15:11:11.607850+00:00",
      "version": "v1",
      "neofs": {
        "object_id": "...",
        "container_id": "...",
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

### SpoonOS Tool Integration

**NeoFS Tools:**
- `CreateContainerTool`: Create storage containers
- `UploadObjectTool`: Upload hypothesis data
- `DownloadObjectByIdTool`: Retrieve data
- `SearchObjectsTool`: Search stored hypotheses

**X402 Tools:**
- `X402PaymentHeaderTool`: Generate payment headers
- `X402PaywalledRequestTool`: Process paywalled requests

---

## Workflow Orchestration

### Spoon StateGraph

**File:** `pipeline_workflow.py`

The pipeline uses Spoon StateGraph for workflow orchestration:

```python
from spoon_ai.graph import StateGraph, START, END

workflow = StateGraph(PipelineState)

# Add nodes
workflow.add_node("read_pdfs", read_pdfs_node)
workflow.add_node("extract_paper_a", extract_paper_a_node)
workflow.add_node("extract_paper_b", extract_paper_b_node)
workflow.add_node("analyze_synergy", analyze_synergy_node)
workflow.add_node("generate_hypothesis", generate_hypothesis_node)
workflow.add_node("mint_hypothesis", mint_hypothesis_node)

# Set entry point
workflow.set_entry_point("read_pdfs")

# Add edges
workflow.add_edge("read_pdfs", "extract_paper_a")
workflow.add_edge("read_pdfs", "extract_paper_b")
workflow.add_parallel_group("extract_papers_parallel", ["extract_paper_a", "extract_paper_b"])
workflow.add_edge("extract_paper_a", "analyze_synergy")
workflow.add_edge("analyze_synergy", "generate_hypothesis")
workflow.add_edge("generate_hypothesis", "mint_hypothesis")
workflow.add_edge("mint_hypothesis", END)

# Compile
compiled = workflow.compile()
```

### Execution Flow

1. **Initial State:** Contains `input_folder`, `author_wallet`, `use_neofs`, `use_x402`
2. **Node Execution:** Each node receives state, processes it, returns updated state
3. **Error Handling:** Nodes set `error` and `error_phase` in state if they fail
4. **Parallel Execution:** Phase 1 nodes run in parallel group
5. **Final State:** Contains all phase outputs and `mint_result`

### Fallback to Sequential

If StateGraph is unavailable, `process_papers.py` falls back to sequential processing (same functions, different orchestration).

---

## Data Structures

### Phase 1 Output: PaperStructure

```typescript
interface PaperStructure {
  claims: string[];              // All claims, no limit
  methods: string[];             // Methods/techniques
  evidence: string[];           // 1-2 items (enforced)
  explicit_limitations: string[];
  implicit_limitations: string[];
  variables: string[];          // Scientific variables/factors
}
```

### Phase 2 Output: SynergyAnalysis

```typescript
interface SynergyAnalysis {
  overlapping_variables: string[];
  potential_synergies: Synergy[];
  potential_conflicts: Conflict[];
  graph: Graph;
}

interface Synergy {
  id: string;                    // e.g., "syn_1"
  description: string;
  paper_A_support: string[];     // Claim IDs: ["A_claim_1", "A_claim_2"]
  paper_B_support: string[];     // Claim IDs: ["B_claim_1"]
}

interface Graph {
  nodes: Node[];
  edges: Edge[];
}

interface Node {
  id: string;                     // e.g., "A_claim_1", "var_temperature"
  type: "claim" | "variable";
  paper: "A" | "B" | "both";
  text: string;
}

interface Edge {
  source: string;                 // Node ID
  target: string;                 // Node ID
  relation: "uses_variable" | "potential_synergy" | "potential_conflict";
  synergy_id?: string;            // If relation is "potential_synergy"
  conflict_id?: string;           // If relation is "potential_conflict"
}
```

### Phase 3 Output: HypothesisCard

```typescript
interface HypothesisCard {
  hypothesis_id: string;          // e.g., "trace_hyp_7e88207e"
  primary_synergy_id: string;      // e.g., "syn_1"
  hypothesis: string;              // "If-then" format
  rationale: string;               // References claim IDs
  source_support: SourceSupport;
  proposed_experiment: Experiment;
  confidence: "low" | "medium" | "high";
  risk_notes: string[];
}

interface SourceSupport {
  paper_A_claim_ids: string[];     // ["A_claim_1", "A_claim_3"]
  paper_B_claim_ids: string[];     // ["B_claim_1", "B_claim_4"]
  variables_used: string[];         // ["temperature", "state_of_health"]
}

interface Experiment {
  description: string;
  measurements: string[];
  expected_direction: string;      // "increase", "decrease", "non-linear", etc.
}
```

### Phase 4 Output: MintResult

```typescript
interface MintResult {
  hypothesis_id: string;
  content_hash: string;            // SHA-256 hash (0x-prefixed hex)
  neo_tx_id: string;               // Neo transaction ID (or mock)
  created_at: string;              // ISO 8601 timestamp (UTC)
  version: string;                  // "v1"
  neofs?: {
    object_id: string;
    container_id: string;
    success: boolean;
  };
  x402?: {
    tx_hash: string;
    amount_usdc: number;
    network: string;
    success: boolean;
  };
}

interface StoredHypothesisCard extends HypothesisCard {
  content_hash: string;
  created_at: string;
  version: string;
  author_wallet: string;
  neo_tx_id: string;
  neofs_object_id?: string;
  neofs_container_id?: string;
  x402_tx_hash?: string;
  x402_amount_usdc?: number;
}
```

---

## SpoonOS Integration

### Phase 1: SpoonOS Tool

**Tool Definition:**
```python
from spoon_ai import Tool

tool = Tool(
    name="extract_paper_structure",
    description="Extract structured scientific information from paper text",
    func=extract_paper_structure_async,
    parameters={
        "paper_text": {"type": "string", "required": True},
        "title": {"type": "string", "required": False}
    }
)
```

**Flow:** Tool → SpoonOS ChatBot → Groq LLM

### Phase 2 & 3: SpoonOS Agent

**Agent Initialization:**
```python
from spoon_ai.agents import SpoonReactAI
from spoon_ai.chat import ChatBot

chatbot = ChatBot(
    llm_provider="openai",
    model_name="llama-3.3-70b-versatile",
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

agent = SpoonReactAI(llm=chatbot)
```

**Flow:** Agent → SpoonOS ChatBot → Groq LLM

### Phase 4: SpoonOS Tools

**NeoFS Tools:**
```python
from spoon_ai.tools.neofs_tools import (
    CreateContainerTool,
    UploadObjectTool,
    DownloadObjectByIdTool
)

create_tool = CreateContainerTool()
upload_tool = UploadObjectTool()
```

**X402 Tools:**
```python
from spoon_ai.tools.x402_payment import (
    X402PaymentHeaderTool,
    X402PaywalledRequestTool
)

header_tool = X402PaymentHeaderTool()
request_tool = X402PaywalledRequestTool()
```

---

## Error Handling

### Phase 0 Errors

- **No PDFs found:** Raises `ValueError` with message
- **Wrong number of PDFs:** Raises `ValueError` specifying count
- **PDF unreadable:** Raises `ValueError` with error details

### Phase 1 Errors

- **Invalid JSON from LLM:** Automatically repairs using `fix_json_async()`
- **Missing fields:** Defaults to empty arrays
- **API errors:** Returns error JSON with error message

### Phase 2 Errors

- **Invalid input structure:** Raises `ValueError` with details
- **LLM analysis fails:** Raises exception with error message
- **Graph building fails:** Falls back to dict-based graph

### Phase 3 Errors

- **Invalid input structure:** Raises `ValueError` with details
- **LLM generation fails:** Raises exception with error message
- **Semantic validation fails:** Auto-fixes or marks low confidence (with retry logic)

### Phase 4 Errors

- **Invalid card structure:** Raises `ValueError` with missing fields
- **Registry save fails:** Raises exception
- **Neo write fails:** Falls back to mock transaction ID (or raises if configured)
- **NeoFS/X402 fails:** Prints warning but continues (graceful degradation)

### Workflow Error Handling

- Each node checks for `error` in state before processing
- Nodes set `error` and `error_phase` in state on failure
- Workflow continues but subsequent nodes skip if error exists
- Final state contains error information for debugging

---

## Configuration

### Required Configuration

**File:** `extraction/.env`

```bash
# Required: Groq API Key
GROQ_API_KEY=your_groq_api_key_here
```

### Optional Configuration

```bash
# Neo Blockchain (optional)
NEO_NETWORK=testnet
NEO_PRIVATE_KEY=your_wif_private_key
NEO_RPC_URL=custom_rpc_url
NEO_REGISTRY_CONTRACT=contract_hash

# NeoFS Storage (optional, SpoonOS Tool)
NEOFS_ENDPOINT=grpc://st1.storage.fs.neo.org:8080
NEOFS_OWNER_ADDRESS=NXxxxxYourNeoAddressHere
NEOFS_PRIVATE_KEY_WIF=your_wif_private_key
NEOFS_CONTAINER_ID=optional_existing_container_id
NEOFS_BEARER_TOKEN=optional_bearer_token

# X402 Payment (optional, SpoonOS Tool)
X402_PRIVATE_KEY=0x...your_eth_private_key
X402_RECEIVER_ADDRESS=0x...
X402_NETWORK=base-sepolia
X402_MINT_FEE=0.001
```

### Environment Variable Loading

All phases load environment variables from `extraction/.env`:

```python
from dotenv import load_dotenv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "..", "extraction", ".env")
load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")
```

---

## Performance Characteristics

### Typical Execution Times

- **PDF Reading:** ~1 second
- **Phase 1:** ~3-6 seconds (2 LLM calls, parallel)
- **Phase 2:** ~3-5 seconds (1 LLM call)
- **Phase 3:** ~3-5 seconds (1 LLM call, may retry up to 2 times)
- **Phase 4:** ~1-2 seconds (local processing + optional NeoFS/X402)

**Total:** ~10-18 seconds for complete pipeline

### Token Usage

- **Phase 1:** ~2000-4000 tokens per paper (abstract only)
- **Phase 2:** ~3000-5000 tokens (both papers + graph)
- **Phase 3:** ~3000-5000 tokens (both papers + synergy analysis)

**Total:** ~11,000-19,000 tokens per pipeline run

---

## Summary

The Trace pipeline is a complete system for generating testable scientific hypotheses from research papers. It uses:

- **SpoonOS** for LLM integration (Agent protocol and Tools)
- **Spoon StateGraph** for workflow orchestration
- **Graph-based reasoning** for synergy analysis
- **Semantic validation** to prevent hallucinations
- **Deterministic hashing** for verification
- **Dual storage** (off-chain + on-chain)
- **SpoonOS Tools** for NeoFS and X402 integration

All phases work together seamlessly, with graceful degradation for optional components. The system is production-ready and can be used with or without optional features like Neo blockchain, NeoFS, or X402 payment.

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-07  
**System Version:** v1
