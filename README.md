# Trace: Scientific Paper Hypothesis Generation Pipeline

**Transform research papers into testable hypotheses on the blockchain**

Trace is an intelligent 4-phase pipeline that extracts structured information from scientific papers, identifies synergies between them, generates testable hypotheses, and mints them to an off-chain registry and Neo blockchain for immutable proof and verification.

---

## 🎯 Overview

Trace takes **2 research paper PDFs** and automatically:

1. **Extracts** structured scientific information (claims, methods, evidence, limitations, variables)
2. **Analyzes** synergies and conflicts between papers using graph-based reasoning
3. **Generates** a testable scientific hypothesis combining elements from both papers
4. **Mints** the hypothesis to a registry and blockchain with cryptographic verification

**Key Features:**
- 🤖 **LLM-Powered**: Uses Groq LLM (llama-3.3-70b-versatile) for intelligent extraction and reasoning
- 📊 **Graph-Based Analysis**: In-memory graph representation for relationship mapping
- 🔒 **Blockchain Integration**: Immutable proof via Neo blockchain + off-chain registry
- 🔍 **Semantic Validation**: Anti-hallucination checks ensure all references are valid
- 📄 **PDF Processing**: Automatically extracts title and abstract from PDFs
- 🎯 **Deterministic Hashing**: SHA-256 content hashing for verification

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Groq API key ([Get one here](https://console.groq.com/))

### Installation

1. **Clone or download the repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API key:**
   
   Create `extraction/.env`:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Add PDFs:**
   
   Place exactly **2 PDF files** in the `input_pdfs/` folder:
   ```
   input_pdfs/
   ├── paper_a.pdf
   └── paper_b.pdf
   ```

5. **Run the pipeline:**
   ```bash
   python process_papers.py
   ```

   Or with custom options:
   ```bash
   python process_papers.py --input-folder input_pdfs --author-wallet NYourWalletAddress
   ```

---

## 📋 How It Works

### Pipeline Flow

```
2 PDF Files (input_pdfs/)
    ↓
[PDF Reading] Extract title + abstract only (~3000 chars each)
    ↓
[Phase 1] Structured Extraction (LLM)
    Paper A JSON + Paper B JSON
    ↓
[Phase 2] Synergy Analysis (LLM + Graph)
    Synergy JSON (with graph structure)
    ↓
[Phase 3] Hypothesis Generation (LLM)
    Hypothesis Card JSON
    ↓
[Phase 4] Minting (Deterministic Hashing + Storage)
    Mint Result + Saved Files
```

### Phase Details

#### **Phase 0: PDF Reading**
- Extracts text from first 2 pages of each PDF
- Intelligently finds and extracts abstract section
- Extracts title from PDF metadata or first line
- Limits to ~3000 characters to stay within API token limits

#### **Phase 1: Structured Extraction**
- Uses Groq LLM to extract structured information from each paper
- Extracts: **claims** (all), **methods**, **evidence** (1-2 items), **limitations** (explicit/implicit), **variables**
- Assigns unique IDs to claims: `A_claim_1`, `A_claim_2`, etc.
- Returns structured JSON for each paper

#### **Phase 2: Synergy Analysis**
- Builds in-memory graph with nodes (claims, variables) and edges (relationships)
- Uses LLM to identify:
  - **Overlapping variables** (semantic matching across papers)
  - **Potential synergies** (complementary findings)
  - **Potential conflicts** (contradictions)
- Enhances graph with synergy/conflict relationships
- Returns analysis JSON with graph structure

#### **Phase 3: Hypothesis Generation**
- Selects primary synergy (highest-scoring based on variables and claims)
- Uses LLM to generate testable "if-then" hypothesis
- Includes: rationale, experiment design, confidence level, risk notes
- **Semantic validation**: Verifies all referenced claim IDs and variables exist
- Auto-fixes invalid references or marks as low confidence

#### **Phase 4: Minting**
- Validates hypothesis card structure
- **Canonicalises JSON** (deterministic format with sorted keys)
- Computes **SHA-256 content hash** for verification
- Saves to **off-chain registry** (`data/hypotheses/{id}.json`)
- Writes **Neo blockchain receipt** (hypothesis_id, hash, author, timestamp)
- Returns mint result with all metadata

---

## 📁 Project Structure

```
Trace/
├── input_pdfs/              # Place 2 PDF files here
│   ├── paper_a.pdf
│   └── paper_b.pdf
│
├── extraction/              # Phase 1: Paper structure extraction
│   ├── pdf_reader.py       # PDF text extraction (title + abstract)
│   ├── extract_groq.py      # Groq LLM integration
│   ├── extract_paper.py    # Core extraction function
│   ├── spoon_tool.py        # SpoonOS tool wrapper
│   └── .env                # GROQ_API_KEY (create this)
│
├── phase2/                  # Phase 2: Synergy analysis
│   └── synergy_agent.py    # Graph building + LLM analysis
│
├── phase3/                  # Phase 3: Hypothesis generation
│   └── hypothesis_agent.py  # Hypothesis generation + validation
│
├── phase4/                  # Phase 4: Hypothesis minting
│   ├── minting_service.py  # Core minting logic
│   ├── registry_store.py   # Off-chain storage
│   └── neo_client.py       # Neo blockchain client
│
├── data/                    # Generated at runtime
│   └── hypotheses/         # Registry (JSON files)
│       └── trace_hyp_*.json
│
├── process_papers.py        # Main entry point
├── requirements.txt         # All dependencies
└── README.md               # This file
```

---

## 🔧 Requirements

### Dependencies

All dependencies are in `requirements.txt`:

- `groq` - LLM API client
- `python-dotenv` - Environment variable management
- `requests` - HTTP requests
- `PyPDF2>=3.0` - PDF text extraction
- `spoon-ai-sdk` - SpoonOS integration (optional)
- `neo3-python` - Neo blockchain SDK (optional, commented out)

### Configuration

- **GROQ_API_KEY**: Required in `extraction/.env`
- **Input**: Exactly 2 PDF files in `input_pdfs/` folder
- **Author Wallet**: Optional Neo wallet address for minting (default: "NXXXX...")

---

## 📊 Example Output

### Generated Hypothesis

```json
{
  "hypothesis_id": "trace_hyp_7e88207e",
  "primary_synergy_id": "syn_1",
  "hypothesis": "If a blockchain-based approach to verify research data integrity from Paper A is applied to Agentic AI systems from Paper B, then the reproducibility rate of research findings will increase.",
  "rationale": "The combination of blockchain-based approaches (A_claim_1, A_claim_3) with Agentic AI systems (B_claim_1, B_claim_4) could leverage the strengths of both...",
  "source_support": {
    "paper_A_claim_ids": ["A_claim_1", "A_claim_3"],
    "paper_B_claim_ids": ["B_claim_1", "B_claim_4"],
    "variables_used": ["Research data", "Data integrity", "Reproducibility rate"]
  },
  "proposed_experiment": {
    "description": "Implement a blockchain-based system to track and verify research data...",
    "measurements": ["Reproducibility rate", "Data integrity checks"],
    "expected_direction": "increase"
  },
  "confidence": "medium",
  "risk_notes": [
    "Assuming Agentic AI systems can effectively integrate with blockchain technology",
    "Potential for increased complexity in the research process"
  ],
  "content_hash": "0x78e26a17e1e881ef210edeccdb5e0606fe079882dac88cf806175a3c023715b2",
  "created_at": "2025-12-06T15:11:11.607850+00:00",
  "version": "v1",
  "author_wallet": "NXXXX...",
  "neo_tx_id": "0x0000000000000000000000000000000000000000000000000000000000000000"
}
```

**Saved to**: `data/hypotheses/trace_hyp_7e88207e.json`

---

## 💻 Usage

### Basic Usage

```bash
# Process 2 PDFs from default folder (input_pdfs/)
python process_papers.py
```

### Custom Options

```bash
# Specify custom input folder
python process_papers.py --input-folder /path/to/pdfs

# Specify author wallet address
python process_papers.py --author-wallet NYourNeoWalletAddress

# Both options
python process_papers.py --input-folder input_pdfs --author-wallet NYourWallet
```

### Programmatic Usage

```python
import asyncio
from process_papers import process_papers_from_folder

# Process papers programmatically
result = asyncio.run(process_papers_from_folder(
    input_folder="input_pdfs",
    author_wallet="NYourWalletAddress"
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
```

---

## 🔍 Key Features Explained

### Intelligent PDF Extraction
- Only extracts **title and abstract** (not full paper)
- Reduces token usage by ~90%
- Automatically finds abstract section
- Extracts title from metadata or first line

### Graph-Based Analysis
- Builds in-memory graph with:
  - **Nodes**: Claims, Variables (from both papers)
  - **Edges**: Relationships (uses_variable, potential_synergy, potential_conflict)
- Enables relationship visualization and querying
- Supports future graph-based reasoning

### Semantic Grounding Validation
- **Post-generation check**: Verifies all referenced claim IDs exist
- **Variable validation**: Ensures all variables exist in input papers
- **Auto-fix**: Removes invalid references automatically
- **Transparency**: Marks low confidence if unfixable issues found

### Deterministic Hashing
- **Canonical JSON**: Sorted keys at all levels for consistency
- **SHA-256 hash**: Unique fingerprint of hypothesis content
- **Verification**: Can recompute hash to verify integrity
- **Immutability**: Hash proves content hasn't changed

### Dual Storage Architecture
- **Off-chain registry**: Full data, fast queries, easy searching (`data/hypotheses/`)
- **On-chain (Neo)**: Immutable proof, timestamp, author verification
- **Separation**: Data storage vs. proof storage

---

## ⚙️ Technical Details

### LLM Configuration
- **Model**: Groq llama-3.3-70b-versatile
- **Temperature**: 0.1 (for consistency in structured extraction)
- **API**: Groq API (fast inference)

### Performance
- **Typical execution time**: 10-18 seconds for 2 papers
- **Token usage**: ~11,000-19,000 tokens per pipeline run
- **PDF processing**: ~1 second
- **LLM calls**: 4 total (Phase 1: 2, Phase 2: 1, Phase 3: 1)

### Error Handling
- Input validation at each phase
- JSON repair fallback for malformed LLM responses
- Clear error messages with phase identification
- Graceful degradation (e.g., mock Neo transaction if SDK not available)

### Security
- API keys stored in `.env` (never committed)
- Input validation prevents injection attacks
- Content hashing enables integrity verification
- Blockchain provides immutable timestamp

---

## 🐛 Troubleshooting

### Common Issues

**"No PDF files found"**
- Ensure exactly 2 PDF files are in `input_pdfs/` folder
- Check file extensions are `.pdf` (case-insensitive)

**"GROQ_API_KEY not found"**
- Create `extraction/.env` file
- Add line: `GROQ_API_KEY=your_key_here`
- Get key from https://console.groq.com/

**"Request too large for model"**
- PDFs are automatically truncated to abstract only
- If still failing, check PDF text extraction is working
- Try with shorter abstracts

**"Neo SDK not available"**
- This is a warning, not an error
- Pipeline continues with mock transaction ID
- Install `neo3-python` for real blockchain integration

**Import errors**
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.8+)

---

## 📖 Output Files

### Registry Files
- **Location**: `data/hypotheses/{hypothesis_id}.json`
- **Content**: Full hypothesis card with all metadata
- **Format**: JSON
- **Purpose**: Fast queries, complete data access

### Blockchain Receipt
- **Location**: Neo blockchain (or mock if SDK not available)
- **Content**: hypothesis_id, content_hash, author, timestamp
- **Purpose**: Immutable proof, verification

---

## 🔄 Pipeline Phases Summary

| Phase | Input | Output | Key Technology |
|-------|-------|--------|----------------|
| **0: PDF Reading** | 2 PDF files | Title + Abstract text | PyPDF2 |
| **1: Extraction** | Paper text | Structured JSON | Groq LLM |
| **2: Analysis** | 2 Paper JSONs | Synergy JSON + Graph | Groq LLM + Graph |
| **3: Generation** | Papers + Synergy | Hypothesis Card | Groq LLM + Validation |
| **4: Minting** | Hypothesis Card | Mint Result + Files | SHA-256 + Neo |

---

## ✅ Status

**All phases complete and tested** ✅

- ✅ Phase 1: PDF reading + structured extraction
- ✅ Phase 2: Synergy and conflict analysis
- ✅ Phase 3: Hypothesis generation with validation
- ✅ Phase 4: Minting to registry and blockchain

**Ready for production use** with:
- Real Groq API key
- Neo blockchain integration (optional)
- 2 PDF files in `input_pdfs/` folder

---

## 📝 License

See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

This is a research project. For questions or issues, please check the code documentation in each phase directory.

---

**Version**: 1.0  
**Last Updated**: 2025-12-06
