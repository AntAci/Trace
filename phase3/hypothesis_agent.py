"""
Phase 3: From Explanation to New Hypotheses
Trace Hypothesis Mode

This module implements a Spoon Agent that generates a testable scientific hypothesis
from Phase 1 and Phase 2 structured outputs.

The agent turns cross-paper synergies into falsifiable scientific hypotheses.

Uses SpoonOS Agent protocol: Agent → SpoonOS → LLM
"""
import json
import os
import uuid
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load Groq API key (same as Phase 1 and Phase 2)
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "..", "extraction", ".env")
load_dotenv(env_path)

# Try to import SpoonOS Agent components
try:
    from spoon_ai.agents import SpoonReactAI
    from spoon_ai.chat import ChatBot
    from spoon_ai.llm import LLMManager, ConfigurationManager
    SPOON_AVAILABLE = True
except ImportError:
    SPOON_AVAILABLE = False
    print("[Warning] spoon-ai-sdk not installed. Falling back to direct Groq.")
    print("Install with: pip install spoon-ai-sdk")
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        client = Groq(api_key=api_key)
    MODEL = "llama-3.3-70b-versatile"

# Initialize SpoonOS components if available
spoon_agent = None
spoon_chatbot = None
if SPOON_AVAILABLE:
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            # Use OpenAI provider with Groq's base URL (OpenAI-compatible API)
            # Groq API endpoint: https://api.groq.com/openai/v1
            try:
                print("[SpoonOS] Configuring ChatBot with OpenAI provider -> Groq base URL")
                spoon_chatbot = ChatBot(
                    llm_provider="openai",
                    model_name="llama-3.3-70b-versatile",
                    api_key=api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                print("[SpoonOS] Successfully created ChatBot with Groq via OpenAI provider")
            except Exception as e1:
                print(f"[Warning] Failed to create ChatBot with OpenAI->Groq: {e1}")
                # Try direct Groq provider as fallback
                try:
                    spoon_chatbot = ChatBot(llm_provider="groq", model_name="llama-3.3-70b-versatile", api_key=api_key)
                except Exception as e2:
                    print(f"[Warning] Failed to create ChatBot with Groq provider: {e2}")
                    spoon_chatbot = None
            
            # Create SpoonOS Agent
            if spoon_chatbot:
                try:
                    spoon_agent = SpoonReactAI(llm=spoon_chatbot)
                    print("[SpoonOS] Successfully created SpoonReactAI Agent")
                except Exception as e:
                    print(f"[Warning] Failed to create SpoonReactAI: {e}")
                    spoon_agent = None
            else:
                print("[Warning] ChatBot creation failed, SpoonOS Agent not available")
    except Exception as e:
        print(f"[Warning] Failed to initialize SpoonOS Agent: {e}")
        print("Falling back to direct Groq calls.")
        SPOON_AVAILABLE = False
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            client = Groq(api_key=api_key)
        MODEL = "llama-3.3-70b-versatile"


class HypothesisAgent:
    """
    Spoon Agent for generating testable scientific hypotheses from paper synergies.
    
    Takes Phase 1 outputs (Paper A, Paper B) and Phase 2 synergy analysis,
    and produces a single, falsifiable hypothesis.
    """
    
    def __init__(self):
        """Initialize the agent with SpoonOS Agent (or fallback to Groq)."""
        self.spoon_agent = spoon_agent
        self.spoon_available = SPOON_AVAILABLE and spoon_agent is not None
        # Always initialize Groq client as fallback
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found. Set it in extraction/.env")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    async def generate_hypothesis_async(self, paper_a_json: Dict[str, Any], paper_b_json: Dict[str, Any],
                                       synergy_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async version: Generate a testable hypothesis from paper synergies using SpoonOS.
        """
        # Validate inputs
        self._validate_phase1_json(paper_a_json, "Paper A")
        self._validate_phase1_json(paper_b_json, "Paper B")
        self._validate_phase2_json(synergy_json)
        
        # Select primary synergy (first one, or most relevant)
        primary_synergy = self._select_primary_synergy(synergy_json)
        
        # Generate hypothesis using SpoonOS
        hypothesis_card = await self._generate_with_spoonos_async(paper_a_json, paper_b_json, synergy_json, primary_synergy)
        
        # Add hypothesis ID
        hypothesis_card["hypothesis_id"] = f"trace_hyp_{uuid.uuid4().hex[:8]}"
        
        # Validate output structure
        self._validate_hypothesis_card(hypothesis_card)
        
        # Post-validation: Check semantic grounding 
        validation_result = self._validate_semantic_grounding(
            hypothesis_card, paper_a_json, paper_b_json, synergy_json
        )
        
        if not validation_result["valid"]:
            # If invalid, try to fix or mark as low confidence
            if validation_result.get("fixable", False):
                hypothesis_card = self._fix_hypothesis_card(
                    hypothesis_card, validation_result, paper_a_json, paper_b_json, synergy_json
                )
            else:
                # Mark as invalid and retry once
                print(f"[Warning] Hypothesis failed semantic validation: {validation_result.get('errors', [])}")
                hypothesis_card["confidence"] = "low"
                hypothesis_card["risk_notes"].append(
                    f"Validation warning: {', '.join(validation_result.get('errors', []))}"
                )
        
        return hypothesis_card
    
    def generate_hypothesis(self, paper_a_json: Dict[str, Any], paper_b_json: Dict[str, Any],
                           synergy_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a testable hypothesis from paper synergies.
        """
        # Validate inputs
        self._validate_phase1_json(paper_a_json, "Paper A")
        self._validate_phase1_json(paper_b_json, "Paper B")
        self._validate_phase2_json(synergy_json)
        
        # Select primary synergy (first one, or most relevant)
        primary_synergy = self._select_primary_synergy(synergy_json)
        
        # Generate hypothesis using Groq
        hypothesis_card = self._generate_with_groq(paper_a_json, paper_b_json, synergy_json, primary_synergy)
        
        # Add hypothesis ID
        hypothesis_card["hypothesis_id"] = f"trace_hyp_{uuid.uuid4().hex[:8]}"
        
        # Validate output structure
        self._validate_hypothesis_card(hypothesis_card)
        
        # Post-validation: Check semantic grounding 
        validation_result = self._validate_semantic_grounding(
            hypothesis_card, paper_a_json, paper_b_json, synergy_json
        )
        
        if not validation_result["valid"]:
            # If invalid, try to fix or mark as low confidence
            if validation_result.get("fixable", False):
                hypothesis_card = self._fix_hypothesis_card(
                    hypothesis_card, validation_result, paper_a_json, paper_b_json, synergy_json
                )
            else:
                # Mark as invalid and retry once
                print(f"[Warning] Hypothesis failed semantic validation: {validation_result.get('errors', [])}")
                hypothesis_card["confidence"] = "low"
                hypothesis_card["risk_notes"].append(
                    f"Validation warning: {', '.join(validation_result.get('errors', []))}"
                )
        
        return hypothesis_card
    
    def _validate_phase1_json(self, paper_json: Dict[str, Any], paper_name: str):
        """Validate that input is a valid Phase 1 JSON structure."""
        required_fields = ["claims", "methods", "evidence", "explicit_limitations", 
                          "implicit_limitations", "variables"]
        
        missing_fields = [f for f in required_fields if f not in paper_json]
        if missing_fields:
            raise ValueError(f"{paper_name} missing required fields: {missing_fields}")
    
    def _validate_phase2_json(self, synergy_json: Dict[str, Any]):
        """Validate that input is a valid Phase 2 JSON structure."""
        required_fields = ["overlapping_variables", "potential_synergies", 
                          "potential_conflicts", "graph"]
        
        missing_fields = [f for f in required_fields if f not in synergy_json]
        if missing_fields:
            raise ValueError(f"Phase 2 JSON missing required fields: {missing_fields}")
    
    def _select_primary_synergy(self, synergy_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Select the primary synergy to focus on.
        
        Selects the synergy with the most overlapping variables or highest relevance.
        Falls back to first synergy if no better selection can be made.
        """
        synergies = synergy_json.get("potential_synergies", [])
        if not synergies:
            return None
        
        if len(synergies) == 1:
            return synergies[0]
        
        # Get overlapping variables
        overlapping_vars = set(synergy_json.get("overlapping_variables", []))
        
        # Score each synergy based on overlapping variables
        best_synergy = None
        best_score = -1
        
        for synergy in synergies:
            score = 0
            
            # Count overlapping variables mentioned in synergy description
            desc = synergy.get("description", "").lower()
            for var in overlapping_vars:
                if var.lower() in desc:
                    score += 1
            
            # Prefer synergies with more supporting claims (more grounded)
            paper_a_support = len(synergy.get("paper_A_support", []))
            paper_b_support = len(synergy.get("paper_B_support", []))
            score += (paper_a_support + paper_b_support) * 0.5
            
            if score > best_score:
                best_score = score
                best_synergy = synergy
        
        # Return best synergy, or first one if scoring didn't help
        return best_synergy if best_synergy else synergies[0]
    
    def _generate_with_groq(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any],
                           synergy: Dict[str, Any], primary_synergy: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use SpoonOS Agent (or Groq fallback) to generate a testable hypothesis.
        Returns a Hypothesis Card JSON object.
        
        Flow: Agent → SpoonOS → LLM (or direct Groq if SpoonOS unavailable)
        """
        prompt = self._build_hypothesis_prompt(paper_a, paper_b, synergy, primary_synergy)
        system_prompt = self._get_system_prompt()
        
        # Use SpoonOS Agent if available
        if self.spoon_available:
            try:
                print("[SpoonOS] Using SpoonOS Agent for hypothesis generation (Agent -> SpoonOS -> LLM)")
                # Use SpoonOS Agent to process the request
                full_prompt = f"{system_prompt}\n\n{prompt}"
                # Check if we're in an async context
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, need to await directly
                    # But since this is a sync method, we'll use direct Groq
                    print("[SpoonOS] In async context, falling back to direct Groq")
                    return self._generate_with_direct_groq(paper_a, paper_b, synergy, primary_synergy, prompt, system_prompt)
                except RuntimeError:
                    # No event loop, we can use asyncio.run
                    print("[SpoonOS] Calling SpoonOS Agent.run()...")
                    response = asyncio.run(self.spoon_agent.run(full_prompt))
                    content = response.content if hasattr(response, 'content') else str(response)
                    print("[SpoonOS] Successfully got response from SpoonOS Agent")
            except Exception as e:
                print(f"[Warning] SpoonOS Agent failed: {e}. Falling back to direct Groq.")
                return self._generate_with_direct_groq(paper_a, paper_b, synergy, primary_synergy, prompt, system_prompt)
        else:
            print("[Direct Groq] SpoonOS not available, using direct Groq calls")
            return self._generate_with_direct_groq(paper_a, paper_b, synergy, primary_synergy, prompt, system_prompt)
    
    async def _generate_with_spoonos_async(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any],
                                          synergy: Dict[str, Any], primary_synergy: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Async method to use SpoonOS Agent properly.
        """
        prompt = self._build_hypothesis_prompt(paper_a, paper_b, synergy, primary_synergy)
        system_prompt = self._get_system_prompt()
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        if self.spoon_available:
            try:
                print("[SpoonOS] Using SpoonOS Agent for hypothesis generation (Agent -> SpoonOS -> LLM)")
                response = await self.spoon_agent.run(full_prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                print("[SpoonOS] Successfully got response from SpoonOS Agent")
                
                # Strip markdown code blocks if present
                content = content.strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    content = "\n".join(lines)
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Response content: {content[:500]}...")
                    return await self._fix_json_async(content)
            except Exception as e:
                print(f"[Warning] SpoonOS Agent failed: {e}. Falling back to direct Groq.")
                return self._generate_with_direct_groq(paper_a, paper_b, synergy, primary_synergy, prompt, system_prompt)
        else:
            print("[Direct Groq] SpoonOS not available, using direct Groq calls")
            return self._generate_with_direct_groq(paper_a, paper_b, synergy, primary_synergy, prompt, system_prompt)
    
    def _generate_with_groq(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any],
                           synergy: Dict[str, Any], primary_synergy: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use SpoonOS Agent (or Groq fallback) to generate a testable hypothesis.
        Returns a Hypothesis Card JSON object.
        
        Flow: Agent → SpoonOS → LLM (or direct Groq if SpoonOS unavailable)
        """
        prompt = self._build_hypothesis_prompt(paper_a, paper_b, synergy, primary_synergy)
        system_prompt = self._get_system_prompt()
        
        # Use SpoonOS Agent if available
        if self.spoon_available:
            try:
                print("[SpoonOS] Using SpoonOS Agent for hypothesis generation (Agent -> SpoonOS -> LLM)")
                # Use SpoonOS Agent to process the request
                full_prompt = f"{system_prompt}\n\n{prompt}"
                # Check if we're in an async context
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, but this is a sync method
                    # Use direct Groq for now (async version available)
                    print("[SpoonOS] In async context, using direct Groq (use generate_hypothesis_async() for SpoonOS)")
                    return self._generate_with_direct_groq(paper_a, paper_b, synergy, primary_synergy, prompt, system_prompt)
                except RuntimeError:
                    # No event loop, we can use asyncio.run
                    print("[SpoonOS] Calling SpoonOS Agent.run()...")
                    response = asyncio.run(self.spoon_agent.run(full_prompt))
                    content = response.content if hasattr(response, 'content') else str(response)
                    print("[SpoonOS] Successfully got response from SpoonOS Agent")
            except Exception as e:
                print(f"[Warning] SpoonOS Agent failed: {e}. Falling back to direct Groq.")
                return self._generate_with_direct_groq(paper_a, paper_b, synergy, primary_synergy, prompt, system_prompt)
        else:
            print("[Direct Groq] SpoonOS not available, using direct Groq calls")
            return self._generate_with_direct_groq(paper_a, paper_b, synergy, primary_synergy, prompt, system_prompt)
        
        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response content: {content[:500]}...")
            return self._fix_json(content)
    
    def _generate_with_direct_groq(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any],
                                   synergy: Dict[str, Any], primary_synergy: Optional[Dict[str, Any]],
                                   prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Fallback: Use direct Groq calls when SpoonOS is not available."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for stable, repeatable output
        )
        
        content = response.choices[0].message.content
        
        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response content: {content[:500]}...")
            return self._fix_json(content)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the hypothesis generation agent."""
        return """You are a scientific hypothesis generation agent that creates testable hypotheses from paper synergies.

CRITICAL RULES:
1. You receive THREE JSON objects: Paper A (Phase 1), Paper B (Phase 1), and Synergy Result (Phase 2)
2. Your task is NOT to summarize the papers - it is to propose ONE new scientific hypothesis
3. The hypothesis MUST be falsifiable and testable
4. The hypothesis MUST combine elements from BOTH papers into something NEW (not just restate existing claims)
5. You MUST only use information from the provided JSON objects - do not introduce new outside knowledge
6. You MUST reference specific claim IDs (e.g., "A_claim_1", "B_claim_2") in your rationale and source_support
7. You MUST NOT invent new datasets, variables, or numerical values not implied by the inputs
8. All output MUST be a single JSON object in the Hypothesis Card format
9. Return ONLY valid JSON - no commentary or explanation outside the JSON structure

The hypothesis should be in the format: "If X condition from Paper A is applied to Y system from Paper B, then Z measurable effect will occur."

Your output must be valid JSON matching the Hypothesis Card schema exactly."""
    
    def _build_hypothesis_prompt(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any],
                                synergy: Dict[str, Any], primary_synergy: Optional[Dict[str, Any]]) -> str:
        """Build the hypothesis generation prompt for Groq."""
        primary_synergy_text = ""
        if primary_synergy:
            primary_synergy_text = f"""
PRIMARY SYNERGY TO FOCUS ON:
{json.dumps(primary_synergy, indent=2)}
"""
        
        return f"""Generate a testable scientific hypothesis based on the following structured paper data.

PAPER A (Phase 1):
{json.dumps(paper_a, indent=2)}

PAPER B (Phase 1):
{json.dumps(paper_b, indent=2)}

SYNERGY ANALYSIS (Phase 2):
{json.dumps(synergy, indent=2)}
{primary_synergy_text}
Your task:
1. Select ONE primary synergy from the potential_synergies list (use its "id" as primary_synergy_id)
2. Generate a NEW, testable hypothesis that combines elements from BOTH papers
3. The hypothesis must be falsifiable and specific enough to be tested experimentally
4. Reference specific claim IDs from the graph (e.g., "A_claim_1", "B_claim_2")
5. Use only variables and concepts that appear in the provided JSON

Return a JSON object with this EXACT structure:
{{
  "primary_synergy_id": "syn_1",
  "hypothesis": "If X condition from Paper A is applied to Y system from Paper B, then Z measurable effect will occur.",
  "rationale": "Short, clear explanation that explicitly references supporting claims and variables from both papers. Must mention specific claim IDs like 'A_claim_1' and 'B_claim_2'.",
  "source_support": {{
    "paper_A_claim_ids": ["A_claim_1", "A_claim_2"],
    "paper_B_claim_ids": ["B_claim_1"],
    "variables_used": ["temperature", "state_of_health"]
  }},
  "proposed_experiment": {{
    "description": "High-level but concrete experimental setup that could test this hypothesis.",
    "measurements": ["what to measure", "another measurement"],
    "expected_direction": "increase / decrease / non-linear effect / etc."
  }},
  "confidence": "low / medium / high",
  "risk_notes": [
    "Key assumption that might fail",
    "Another potential weakness"
  ]
}}

Return ONLY the JSON object. Do not add commentary."""
    
    def _validate_hypothesis_card(self, card: Dict[str, Any]):
        """Validate that the hypothesis card has all required fields."""
        required_fields = [
            "primary_synergy_id", "hypothesis", "rationale", "source_support",
            "proposed_experiment", "confidence", "risk_notes"
        ]
        
        missing_fields = [f for f in required_fields if f not in card]
        if missing_fields:
            # Add defaults for missing fields rather than failing
            if "primary_synergy_id" not in card:
                card["primary_synergy_id"] = "unknown"
            if "confidence" not in card:
                card["confidence"] = "medium"
            if "risk_notes" not in card:
                card["risk_notes"] = []
        
        # Validate nested structures
        if "source_support" in card and not isinstance(card["source_support"], dict):
            card["source_support"] = {
                "paper_A_claim_ids": [],
                "paper_B_claim_ids": [],
                "variables_used": []
            }
        
        if "proposed_experiment" in card and not isinstance(card["proposed_experiment"], dict):
            card["proposed_experiment"] = {
                "description": "",
                "measurements": [],
                "expected_direction": ""
            }
    
    def _validate_semantic_grounding(self, hypothesis_card: Dict[str, Any],
                                    paper_a: Dict[str, Any], paper_b: Dict[str, Any],
                                    synergy_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-validation: Check that all referenced claims and variables actually exist.
        
        This helps catch LLM hallucinations where it references non-existent claim IDs
        or variables not present in the input papers.
        
        Returns:
            dict: {"valid": bool, "errors": list, "fixable": bool}
        """
        errors = []
        fixable = True
        
        # Get all valid claim IDs from graph
        graph = synergy_json.get("graph", {})
        nodes = graph.get("nodes", [])
        valid_claim_ids = {n["id"] for n in nodes if n.get("type") == "claim"}
        
        # Get all valid variables from both papers
        valid_variables = set()
        for var in paper_a.get("variables", []):
            valid_variables.add(str(var).lower())
        for var in paper_b.get("variables", []):
            valid_variables.add(str(var).lower())
        
        # Check source_support
        source_support = hypothesis_card.get("source_support", {})
        
        # Validate Paper A claim IDs
        paper_a_claims = source_support.get("paper_A_claim_ids", [])
        invalid_a_claims = [cid for cid in paper_a_claims if cid not in valid_claim_ids]
        if invalid_a_claims:
            errors.append(f"Invalid Paper A claim IDs: {invalid_a_claims}")
            fixable = True  # Can remove invalid IDs
        
        # Validate Paper B claim IDs
        paper_b_claims = source_support.get("paper_B_claim_ids", [])
        invalid_b_claims = [cid for cid in paper_b_claims if cid not in valid_claim_ids]
        if invalid_b_claims:
            errors.append(f"Invalid Paper B claim IDs: {invalid_b_claims}")
            fixable = True  # Can remove invalid IDs
        
        # Validate variables
        variables_used = source_support.get("variables_used", [])
        invalid_vars = []
        for var in variables_used:
            if str(var).lower() not in valid_variables:
                invalid_vars.append(var)
        
        if invalid_vars:
            errors.append(f"Invalid variables (not in input papers): {invalid_vars}")
            fixable = True  # Can remove invalid variables
        
        # Check if primary_synergy_id exists
        primary_synergy_id = hypothesis_card.get("primary_synergy_id")
        if primary_synergy_id:
            synergy_ids = {s.get("id") for s in synergy_json.get("potential_synergies", [])}
            if primary_synergy_id not in synergy_ids:
                errors.append(f"Invalid primary_synergy_id: {primary_synergy_id}")
                fixable = True  # Can update to first valid synergy
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "fixable": fixable
        }
    
    def _fix_hypothesis_card(self, hypothesis_card: Dict[str, Any], validation_result: Dict[str, Any],
                           paper_a: Dict[str, Any], paper_b: Dict[str, Any],
                           synergy_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix hypothesis card by removing invalid references.
        
        Removes invalid claim IDs and variables, keeping only valid ones.
        """
        # Get valid IDs
        graph = synergy_json.get("graph", {})
        nodes = graph.get("nodes", [])
        valid_claim_ids = {n["id"] for n in nodes if n.get("type") == "claim"}
        
        valid_variables = set()
        for var in paper_a.get("variables", []):
            valid_variables.add(str(var).lower())
        for var in paper_b.get("variables", []):
            valid_variables.add(str(var).lower())
        
        # Fix source_support
        source_support = hypothesis_card.get("source_support", {})
        
        # Remove invalid Paper A claim IDs
        paper_a_claims = source_support.get("paper_A_claim_ids", [])
        source_support["paper_A_claim_ids"] = [cid for cid in paper_a_claims if cid in valid_claim_ids]
        
        # Remove invalid Paper B claim IDs
        paper_b_claims = source_support.get("paper_B_claim_ids", [])
        source_support["paper_B_claim_ids"] = [cid for cid in paper_b_claims if cid in valid_claim_ids]
        
        # Remove invalid variables
        variables_used = source_support.get("variables_used", [])
        source_support["variables_used"] = [
            var for var in variables_used if str(var).lower() in valid_variables
        ]
        
        # Fix primary_synergy_id if invalid
        primary_synergy_id = hypothesis_card.get("primary_synergy_id")
        if primary_synergy_id:
            synergy_ids = {s.get("id") for s in synergy_json.get("potential_synergies", [])}
            if primary_synergy_id not in synergy_ids:
                # Use first valid synergy
                synergies = synergy_json.get("potential_synergies", [])
                if synergies:
                    hypothesis_card["primary_synergy_id"] = synergies[0].get("id", "unknown")
                else:
                    hypothesis_card["primary_synergy_id"] = "unknown"
        
        return hypothesis_card
    
    async def _fix_json_async(self, bad_text: str) -> Dict[str, Any]:
        """Async version: Repair malformed JSON using SpoonOS Agent (or Groq fallback)."""
        fix_prompt = f"""The following text should be valid JSON but is not. Fix it.

TEXT:
{bad_text}

Return only corrected JSON with the Hypothesis Card structure:
{{
  "primary_synergy_id": "syn_1",
  "hypothesis": "...",
  "rationale": "...",
  "source_support": {{"paper_A_claim_ids": [], "paper_B_claim_ids": [], "variables_used": []}},
  "proposed_experiment": {{"description": "...", "measurements": [], "expected_direction": "..."}},
  "confidence": "medium",
  "risk_notes": []
}}"""

        # Use SpoonOS Agent if available
        if self.spoon_available:
            try:
                full_prompt = f"Fix JSON formatting only.\n\n{fix_prompt}"
                response = await self.spoon_agent.run(full_prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                return json.loads(content)
            except Exception as e:
                print(f"[Warning] SpoonOS Agent failed in fix_json: {e}. Using direct Groq.")
        
        # Fallback to direct Groq
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Fix JSON formatting only."},
                {"role": "user", "content": fix_prompt}
            ],
            temperature=0.0,
        )

        return json.loads(response.choices[0].message.content)
    
    def _fix_json(self, bad_text: str) -> Dict[str, Any]:
        """Repair malformed JSON using SpoonOS Agent (or Groq fallback)."""
        fix_prompt = f"""The following text should be valid JSON but is not. Fix it.

TEXT:
{bad_text}

Return only corrected JSON with the Hypothesis Card structure:
{{
  "primary_synergy_id": "syn_1",
  "hypothesis": "...",
  "rationale": "...",
  "source_support": {{"paper_A_claim_ids": [], "paper_B_claim_ids": [], "variables_used": []}},
  "proposed_experiment": {{"description": "...", "measurements": [], "expected_direction": "..."}},
  "confidence": "medium",
  "risk_notes": []
}}"""

        # Use SpoonOS Agent if available
        if self.spoon_available:
            try:
                full_prompt = f"Fix JSON formatting only.\n\n{fix_prompt}"
                # Check if we're in an async context
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, use direct Groq
                    pass  # Fall through to direct Groq
                except RuntimeError:
                    # No event loop, we can use asyncio.run
                    response = asyncio.run(self.spoon_agent.run(full_prompt))
                    content = response.content if hasattr(response, 'content') else str(response)
                    return json.loads(content)
            except Exception as e:
                print(f"[Warning] SpoonOS Agent failed in fix_json: {e}. Using direct Groq.")
        
        # Fallback to direct Groq
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Fix JSON formatting only."},
                {"role": "user", "content": fix_prompt}
            ],
            temperature=0.0,
        )

        return json.loads(response.choices[0].message.content)


def generate_hypothesis(paper_a_json: Dict[str, Any], paper_b_json: Dict[str, Any],
                        synergy_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to generate a hypothesis.
    
    Args:
        paper_a_json: Phase 1 output for Paper A
        paper_b_json: Phase 1 output for Paper B
        synergy_json: Phase 2 output with synergies, conflicts, and graph
    
    Returns:
        dict: Hypothesis Card with hypothesis, rationale, experiment, etc.
    """
    agent = HypothesisAgent()
    return agent.generate_hypothesis(paper_a_json, paper_b_json, synergy_json)


if __name__ == "__main__":
    # Example usage
    paper_a = {
        "claims": ["High temperature accelerates battery degradation"],
        "methods": ["Accelerated aging tests"],
        "evidence": ["50% capacity loss at 60°C after 100 cycles"],
        "explicit_limitations": ["Limited to NMC chemistry"],
        "implicit_limitations": [],
        "variables": ["temperature", "capacity", "cycles"]
    }
    
    paper_b = {
        "claims": ["State of health can be predicted using temperature and voltage"],
        "methods": ["Machine learning regression"],
        "evidence": ["95% accuracy on test set"],
        "explicit_limitations": ["Requires large training dataset"],
        "implicit_limitations": [],
        "variables": ["temperature", "voltage", "state_of_health"]
    }
    
    synergy_result = {
        "overlapping_variables": ["temperature"],
        "potential_synergies": [
            {
                "id": "syn_1",
                "description": "Paper A's temperature findings could inform Paper B's model",
                "paper_A_support": ["A_claim_1"],
                "paper_B_support": ["B_claim_1"]
            }
        ],
        "potential_conflicts": [],
        "graph": {
            "nodes": [
                {"id": "A_claim_1", "type": "claim", "paper": "A", "text": "High temperature accelerates battery degradation"},
                {"id": "B_claim_1", "type": "claim", "paper": "B", "text": "State of health can be predicted using temperature and voltage"}
            ],
            "edges": []
        }
    }
    
    result = generate_hypothesis(paper_a, paper_b, synergy_result)
    print(json.dumps(result, indent=2))

