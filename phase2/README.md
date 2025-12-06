# Phase 2: Synergy and Conflict Engine

**Purpose:** Compare two Phase 1 structured JSON outputs and identify synergies, conflicts, and overlapping variables.

Phase 2 builds on Phase 1 by analyzing the relationship between two papers. It does NOT modify Phase 1 or generate hypotheses (that's Phase 3).

---

## 🎯 What Phase 2 Does

Given two Phase 1 JSON outputs (Paper A and Paper B), Phase 2:

- **Identifies overlapping variables** across both papers
- **Detects potential synergies** (where papers complement each other)
- **Detects potential conflicts** (where papers contradict each other)
- **Builds an in-memory graph** linking claims and variables

**Output:** Structured JSON with synergies, conflicts, and graph representation

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Use the Agent

```python
from phase2.synergy_agent import analyze_papers

# Get Phase 1 outputs (from extract_paper_structure tool)
paper_a_json = {...}  # Phase 1 output for Paper A
paper_b_json = {...}  # Phase 1 output for Paper B

# Analyze for synergies and conflicts
result = analyze_papers(paper_a_json, paper_b_json)

# Result contains:
# - overlapping_variables
# - potential_synergies
# - potential_conflicts
# - graph (nodes and edges)
```

---

## 📋 Output Format

```json
{
  "overlapping_variables": [
    "temperature",
    "state_of_health"
  ],
  "potential_synergies": [
    {
      "id": "syn_1",
      "description": "Paper A's result about high-temperature degradation refines the model in Paper B.",
      "paper_A_support": ["A_claim_1", "A_evidence_1"],
      "paper_B_support": ["B_claim_2"]
    }
  ],
  "potential_conflicts": [
    {
      "id": "conf_1",
      "description": "Paper B assumes linear ageing where Paper A indicates non-linear behaviour.",
      "paper_A_support": ["A_claim_3"],
      "paper_B_support": ["B_claim_1"]
    }
  ],
  "graph": {
    "nodes": [
      {"id": "A_claim_1", "type": "claim", "paper": "A", "text": "..."},
      {"id": "B_claim_2", "type": "claim", "paper": "B", "text": "..."},
      {"id": "var_temperature", "type": "variable", "paper": "both", "text": "temperature"}
    ],
    "edges": [
      {"source": "A_claim_1", "target": "var_temperature", "relation": "uses_variable"},
      {"source": "B_claim_2", "target": "var_temperature", "relation": "uses_variable"},
      {"source": "A_claim_1", "target": "B_claim_2", "relation": "potential_synergy"}
    ]
  }
}
```

---

## 🔧 Components

### `SynergyAgent` Class

The main agent class that performs the analysis.

**Methods**:
- `analyze(paper_a_json, paper_b_json)` - Main analysis method
- `_build_graph()` - Builds in-memory graph representation
- `_analyze_with_groq()` - Uses Groq LLM for reasoning
- `_validate_phase1_json()` - Validates input structure

### `analyze_papers()` Function

Convenience function that creates an agent and runs analysis.

---

## 🔄 Architecture

**Phase 2 Flow**:
1. Receives two Phase 1 JSON outputs
2. Validates input structure
3. Builds in-memory graph (nodes: claims, variables; edges: relationships)
4. Uses Groq LLM to analyze:
   - Overlapping variables
   - Potential synergies
   - Potential conflicts
5. Returns structured JSON

**No Persistence**: Graph is in-memory only, not saved to disk.

---

## 🔐 Configuration

Phase 2 uses the same `GROQ_API_KEY` as Phase 1 (from `extraction/.env`).

No additional configuration needed.

---

## 📝 Key Design Decisions

- ✅ **Consumes Phase 1 output only** - Never calls `extract_paper_structure` directly
- ✅ **No hypothesis generation** - Only identifies synergies/conflicts
- ✅ **In-memory graph** - Not persisted, rebuilt per request
- ✅ **Structured JSON output** - No free-form text
- ✅ **No hallucination** - Only uses claims/variables from input
- ✅ **Local execution** - No Spoon API keys, runs entirely locally

---

## 🧪 Testing

Test with two Phase 1 outputs:

```python
from phase2.synergy_agent import analyze_papers

paper_a = {
    "claims": ["High temperature accelerates degradation"],
    "methods": ["Aging tests"],
    "evidence": ["50% loss at 60°C"],
    "explicit_limitations": [],
    "implicit_limitations": [],
    "variables": ["temperature", "capacity"]
}

paper_b = {
    "claims": ["SOH can be predicted from temperature"],
    "methods": ["ML regression"],
    "evidence": ["95% accuracy"],
    "explicit_limitations": [],
    "implicit_limitations": [],
    "variables": ["temperature", "state_of_health"]
}

result = analyze_papers(paper_a, paper_b)
print(json.dumps(result, indent=2))
```

---

**Status: ✅ Ready for Phase 3 Integration**

