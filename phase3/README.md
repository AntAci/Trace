# Phase 3: From Explanation to New Hypotheses

**Trace Hypothesis Mode**

**Purpose:** Generate a testable scientific hypothesis from Phase 1 and Phase 2 structured outputs.

Phase 3 is the "AI innovation" highlight - it turns cross-paper structure into a new, falsifiable scientific idea.

---

## 🎯 What Phase 3 Does

Given:
- Phase 1 outputs for Paper A and Paper B
- Phase 2 output (synergies, conflicts, graph)

Phase 3 generates:
- **One testable scientific hypothesis** that combines elements from both papers
- **Rationale** explicitly referencing supporting claims
- **Proposed experiment** to test the hypothesis
- **Confidence level** and risk notes

**Output:** Hypothesis Card JSON ready for Phase 4 (minting)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Use the Agent

```python
from phase3.hypothesis_agent import generate_hypothesis

# Get Phase 1 outputs (from extract_paper_structure tool)
paper_a_json = {...}  # Phase 1 output for Paper A
paper_b_json = {...}  # Phase 1 output for Paper B

# Get Phase 2 output (from SynergyAgent)
synergy_json = {...}  # Phase 2 output with synergies, conflicts, graph

# Generate hypothesis
hypothesis_card = generate_hypothesis(paper_a_json, paper_b_json, synergy_json)

# Result contains:
# - hypothesis_id
# - primary_synergy_id
# - hypothesis (testable statement)
# - rationale
# - source_support (claim IDs and variables)
# - proposed_experiment
# - confidence
# - risk_notes
```

---

## 📋 Output Format (Hypothesis Card)

```json
{
  "hypothesis_id": "trace_hyp_001",
  "primary_synergy_id": "syn_1",
  "hypothesis": "If high-temperature degradation mechanism from Paper A is applied to Paper B's SOH prediction system, then the model accuracy will improve at temperatures above 45°C.",
  "rationale": "Paper A (A_claim_1, A_claim_2) demonstrates non-linear degradation above 45°C, while Paper B (B_claim_1) uses a linear model. Combining A's temperature-dependent mechanism with B's prediction framework could improve accuracy.",
  "source_support": {
    "paper_A_claim_ids": ["A_claim_1", "A_claim_2"],
    "paper_B_claim_ids": ["B_claim_1"],
    "variables_used": ["temperature", "state_of_health"]
  },
  "proposed_experiment": {
    "description": "Test SOH prediction model from Paper B using temperature-dependent degradation rates from Paper A. Run predictions at various temperatures (30°C, 45°C, 60°C) and compare accuracy.",
    "measurements": ["SOH prediction accuracy", "Temperature-dependent error rates", "Model performance at different temperatures"],
    "expected_direction": "improvement in accuracy at high temperatures"
  },
  "confidence": "medium",
  "risk_notes": [
    "Assumes Paper A's degradation mechanism applies to Paper B's system",
    "May require retraining Paper B's model with temperature-dependent data"
  ]
}
```

---

## 🔧 Components

### `HypothesisAgent` Class

The main agent class that generates hypotheses.

**Methods**:
- `generate_hypothesis(paper_a_json, paper_b_json, synergy_json)` - Main generation method
- `_select_primary_synergy()` - Selects which synergy to focus on
- `_generate_with_groq()` - Uses Groq LLM for hypothesis generation
- `_validate_phase1_json()` - Validates Phase 1 input
- `_validate_phase2_json()` - Validates Phase 2 input
- `_validate_hypothesis_card()` - Validates output structure

### `generate_hypothesis()` Function

Convenience function that creates an agent and generates a hypothesis.

---

## 🔄 Architecture

**Phase 3 Flow**:
1. Receives Phase 1 outputs (Paper A, Paper B)
2. Receives Phase 2 output (synergies, conflicts, graph)
3. Validates all inputs
4. Selects primary synergy to focus on
5. Uses Groq LLM to generate hypothesis
6. Validates output structure
7. Returns Hypothesis Card JSON

**No Persistence**: All processing is in-memory, per request.

---

## 🔐 Configuration

Phase 3 uses the same `GROQ_API_KEY` as Phase 1 and Phase 2 (from `extraction/.env`).

No additional configuration needed.

---

## 📝 Key Design Decisions

- ✅ **Consumes Phase 1 and Phase 2 outputs only** - Never calls Phase 1 or Phase 2 directly
- ✅ **One hypothesis per run** - Focuses on primary synergy
- ✅ **Falsifiable and testable** - Hypothesis must be experimentally verifiable
- ✅ **References specific claims** - Uses claim IDs from Phase 2 graph
- ✅ **No hallucination** - Only uses information from provided JSON
- ✅ **Low temperature** - 0.1 for stable, repeatable output
- ✅ **Local execution** - No Spoon API keys, runs entirely locally

---

## 🧪 Testing

Test with Phase 1 and Phase 2 outputs:

```python
from phase3.hypothesis_agent import generate_hypothesis

# Phase 1 outputs
paper_a = {...}
paper_b = {...}

# Phase 2 output
synergy_result = {
    "overlapping_variables": [...],
    "potential_synergies": [...],
    "potential_conflicts": [...],
    "graph": {...}
}

# Generate hypothesis
result = generate_hypothesis(paper_a, paper_b, synergy_result)
print(json.dumps(result, indent=2))
```

---

## ✅ Requirements Met

- ✅ Takes Phase 1 outputs (Paper A, Paper B) and Phase 2 output
- ✅ Generates exactly ONE hypothesis card
- ✅ References actual claim IDs from inputs
- ✅ Includes testable experiment outline
- ✅ Produces consistent JSON across runs
- ✅ Does NOT call Phase 1 or Phase 2 tools
- ✅ Does NOT perform blockchain/NFT operations (that's Phase 4)
- ✅ All processing in-memory (no persistence)

---

**Status: ✅ Ready for Phase 4 Integration**

