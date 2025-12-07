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
        """Initialize the agent with SpoonOS Agent (REQUIRED)."""
        # STRICT REQUIREMENT: SpoonOS must be available
        if not SPOON_AVAILABLE:
            raise RuntimeError(
                "SpoonOS is REQUIRED for this project.\n"
                "Install with: pip install spoon-ai-sdk\n"
                "Ensure GROQ_API_KEY is set in extraction/.env"
            )
        
        if spoon_agent is None:
            raise RuntimeError(
                "SpoonOS Agent is not initialized.\n"
                "Check that GROQ_API_KEY is set in extraction/.env\n"
                "SpoonOS Agent initialization may have failed during import.\n"
                "Check the console output for initialization errors."
            )
        
        self.spoon_agent = spoon_agent
        self.spoon_available = True  # Always True if we get here
        
        # Keep Groq client for JSON fix operations (not for primary LLM calls)
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
        
        Implements retry logic: up to 2 retries if validation finds invalid claims (hallucinations).
        """
        # Validate inputs
        self._validate_phase1_json(paper_a_json, "Paper A")
        self._validate_phase1_json(paper_b_json, "Paper B")
        self._validate_phase2_json(synergy_json)
        
        # Select primary synergy (first one, or most relevant)
        primary_synergy = self._select_primary_synergy(synergy_json)
        
        max_retries = 2
        retry_count = 0
        last_validation_errors = []
        
        # Generate hypothesis with retry loop
        while retry_count <= max_retries:
            # Generate hypothesis using SpoonOS
            if retry_count == 0:
                # First attempt: use standard prompt
                hypothesis_card = await self._generate_with_spoonos_async(
                    paper_a_json, paper_b_json, synergy_json, primary_synergy
                )
            else:
                # Retry: use enhanced prompt with validation feedback
                print(f"[Retry {retry_count}/{max_retries}] Regenerating hypothesis with validation feedback...")
                hypothesis_card = await self._generate_with_spoonos_retry_async(
                    paper_a_json, paper_b_json, synergy_json, primary_synergy,
                    last_validation_errors, synergy_json
                )
                # Generate new hypothesis ID for retry
                hypothesis_card["hypothesis_id"] = f"trace_hyp_{uuid.uuid4().hex[:8]}"
            
            # Add hypothesis ID (only on first attempt)
            if retry_count == 0:
                hypothesis_card["hypothesis_id"] = f"trace_hyp_{uuid.uuid4().hex[:8]}"
            
            # Validate output structure
            self._validate_hypothesis_card(hypothesis_card)
            
            # Post-validation: Check semantic grounding 
            validation_result = self._validate_semantic_grounding(
                hypothesis_card, paper_a_json, paper_b_json, synergy_json
            )
            
            if validation_result["valid"]:
                # Success! Return the valid hypothesis
                if retry_count > 0:
                    print(f"[Success] Hypothesis validated after {retry_count} retry(ies)")
                return hypothesis_card
            
            # Validation failed - store errors for retry prompt
            last_validation_errors = validation_result.get("errors", [])
            
            # Check if we should retry
            if retry_count < max_retries:
                print(f"[Warning] Hypothesis failed validation (attempt {retry_count + 1}/{max_retries + 1}):")
                for error in last_validation_errors:
                    print(f"  - {error}")
                retry_count += 1
                continue
            
            # Max retries reached - fix and mark as low confidence
            print(f"[Warning] Hypothesis failed validation after {max_retries} retries. Fixing invalid references...")
            if validation_result.get("fixable", False):
                hypothesis_card = self._fix_hypothesis_card(
                    hypothesis_card, validation_result, paper_a_json, paper_b_json, synergy_json
                )
            else:
                hypothesis_card["confidence"] = "low"
                hypothesis_card["risk_notes"].append(
                    f"Validation warning after {max_retries} retries: {', '.join(last_validation_errors)}"
                )
            break
        
        return hypothesis_card
    
    def generate_hypothesis(self, paper_a_json: Dict[str, Any], paper_b_json: Dict[str, Any],
                           synergy_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a testable hypothesis from paper synergies (sync version).
        
        Note: This method uses async internally. For better performance, use generate_hypothesis_async.
        """
        # Use async version via asyncio.run
        import asyncio
        try:
            # Check if we're already in an async context
            asyncio.get_running_loop()
            # If we're in an async context, we can't use asyncio.run
            raise RuntimeError(
                "Cannot use sync generate_hypothesis in async context. "
                "Use generate_hypothesis_async instead."
            )
        except RuntimeError as e:
            # Check if this is our custom error or the "no running loop" error
            if "async context" in str(e):
                raise  # Re-raise our custom error
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self.generate_hypothesis_async(paper_a_json, paper_b_json, synergy_json))
    
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
        
        REQUIRES: SpoonOS must be installed and properly configured.
        Raises RuntimeError if SpoonOS is unavailable.
        """
        # STRICT REQUIREMENT: SpoonOS must be available
        if not self.spoon_available:
            raise RuntimeError(
                "SpoonOS is REQUIRED for this project.\n"
                "Install with: pip install spoon-ai-sdk\n"
                "Ensure GROQ_API_KEY is set in extraction/.env"
            )
        
        if not self.spoon_agent:
            raise RuntimeError(
                "SpoonOS Agent is not initialized.\n"
                "Check that GROQ_API_KEY is set in extraction/.env\n"
                "SpoonOS Agent initialization may have failed during import."
            )
        
        prompt = self._build_hypothesis_prompt(paper_a, paper_b, synergy, primary_synergy)
        system_prompt = self._get_system_prompt()
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            print("[SpoonOS] Using SpoonOS Agent for hypothesis generation (Agent -> SpoonOS -> LLM)")
            response = await self.spoon_agent.run(full_prompt)
            
            # Extract content from response (try multiple formats)
            content = None
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            elif hasattr(response, 'message'):
                content = response.message
            elif isinstance(response, dict):
                # Response is a dict, try common fields
                content = response.get('content') or response.get('text') or response.get('message') or str(response)
            else:
                content = str(response)
            
            print(f"[SpoonOS] Successfully got response from SpoonOS Agent (type: {type(response)})")
            
            # If content is still a dict, try to find JSON string in it
            if isinstance(content, dict):
                # Look for JSON in string fields
                for key, value in content.items():
                    if isinstance(value, str) and ('{' in value or '[' in value):
                        content = value
                        break
                # If still dict, convert to JSON string
                if isinstance(content, dict):
                    content = json.dumps(content)
            
            # Strip markdown code blocks if present
            content = str(content).strip()
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)
            
            # Try to extract JSON from text if it contains JSON
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Response content (first 500 chars): {content[:500]}...")
                print(f"Response type: {type(response)}")
                # Try direct Groq fallback for JSON fixing instead of agent
                return await self._fix_json_with_groq_async(content)
        except Exception as e:
            raise RuntimeError(
                f"SpoonOS Agent call failed.\n"
                f"Error: {e}\n"
                f"Please check your GROQ_API_KEY and network connection."
            ) from e
    
    async def _generate_with_spoonos_retry_async(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any],
                                                 synergy: Dict[str, Any], primary_synergy: Optional[Dict[str, Any]],
                                                 validation_errors: list, synergy_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retry generation with enhanced prompt that includes validation feedback.
        
        This method is called when the initial hypothesis had invalid claim references.
        It provides explicit valid claim IDs and validation errors to guide the LLM.
        """
        if not self.spoon_available or not self.spoon_agent:
            raise RuntimeError(
                "SpoonOS is REQUIRED for this project.\n"
                "Install with: pip install spoon-ai-sdk\n"
                "Ensure GROQ_API_KEY is set in extraction/.env"
            )
        
        # Get valid claim IDs from graph
        graph = synergy_json.get("graph", {})
        nodes = graph.get("nodes", [])
        valid_claim_ids = sorted([n["id"] for n in nodes if n.get("type") == "claim"])
        
        # Get valid variables
        valid_variables = set()
        for var in paper_a.get("variables", []):
            valid_variables.add(str(var))
        for var in paper_b.get("variables", []):
            valid_variables.add(str(var))
        valid_variables_list = sorted(list(valid_variables))
        
        # Get valid synergy IDs
        synergy_ids = sorted([s.get("id") for s in synergy_json.get("potential_synergies", [])])
        
        # Build enhanced retry prompt
        primary_synergy_text = ""
        if primary_synergy:
            primary_synergy_text = f"""
PRIMARY SYNERGY TO FOCUS ON:
{json.dumps(primary_synergy, indent=2)}
"""
        
        validation_feedback = "\n".join([f"  - {error}" for error in validation_errors])
        
        retry_prompt = f"""⚠️ RETRY REQUEST: Previous hypothesis had invalid claim references.

VALIDATION ERRORS FROM PREVIOUS ATTEMPT:
{validation_feedback}

CRITICAL: You MUST use ONLY the following valid IDs:

VALID CLAIM IDs (from graph nodes):
{json.dumps(valid_claim_ids, indent=2)}

VALID VARIABLES (from input papers):
{json.dumps(valid_variables_list, indent=2)}

VALID SYNERGY IDs (from potential_synergies):
{json.dumps(synergy_ids, indent=2)}

Generate a testable scientific hypothesis based on the following structured paper data.

PAPER A (Phase 1):
{json.dumps(paper_a, indent=2)}

PAPER B (Phase 1):
{json.dumps(paper_b, indent=2)}

SYNERGY ANALYSIS (Phase 2):
{json.dumps(synergy, indent=2)}
{primary_synergy_text}

Your task:
1. Select ONE primary synergy from the potential_synergies list (use its "id" as primary_synergy_id)
   - MUST be one of: {synergy_ids}
2. Generate a NEW, testable hypothesis that combines elements from BOTH papers
3. The hypothesis must be falsifiable and specific enough to be tested experimentally
4. Reference specific claim IDs from the graph
   - Paper A claims MUST be from: {[cid for cid in valid_claim_ids if cid.startswith('A_')]}
   - Paper B claims MUST be from: {[cid for cid in valid_claim_ids if cid.startswith('B_')]}
   - DO NOT invent claim IDs that don't exist in the list above
5. Use only variables from the valid variables list: {valid_variables_list}
   - DO NOT use variables that aren't in this list

Return a JSON object with this EXACT structure:
{{
  "primary_synergy_id": "syn_1",  // MUST be from: {synergy_ids}
  "hypothesis": "If X condition from Paper A is applied to Y system from Paper B, then Z measurable effect will occur.",
  "rationale": "Short, clear explanation that explicitly references supporting claims and variables from both papers. Must mention specific claim IDs like 'A_claim_1' and 'B_claim_2'.",
  "source_support": {{
    "paper_A_claim_ids": ["A_claim_1", "A_claim_2"],  // MUST be from valid Paper A claims
    "paper_B_claim_ids": ["B_claim_1"],  // MUST be from valid Paper B claims
    "variables_used": ["temperature", "state_of_health"]  // MUST be from valid variables list
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
        
        system_prompt = self._get_system_prompt()
        full_prompt = f"{system_prompt}\n\n{retry_prompt}"
        
        try:
            print("[SpoonOS Retry] Regenerating with validation feedback...")
            response = await self.spoon_agent.run(full_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            print("[SpoonOS Retry] Successfully got response from SpoonOS Agent")
            
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
            raise RuntimeError(
                f"SpoonOS Agent failed during retry.\n"
                f"Original error: {e}\n"
                f"Please check your GROQ_API_KEY and network connection."
            ) from e
    
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
        
        return f"""Generate a specific, falsifiable "Bridging Hypothesis".

INPUT SYNERGY: {json.dumps(synergy, indent=2)}
{primary_synergy_text}

Output a STRICT JSON object:

{{
  "_confidence_check": "Rate the technical strength of the synergy (High/Medium/Low). If Low, explain why.",

  "primary_synergy_id": "syn_1",

  "hypothesis": "If [specific method from methods field] is applied to [system/context from variables field], then [specific variable from variables field] will [increase/decrease/change] due to [technical mechanism from the synergy description].",

  "rationale": "Technical justification referencing specific entities from the input JSON (e.g. method names from methods field, limitation names from explicit_limitations field, variable names from variables field).",

  "source_support": {{
    "paper_A_claim_ids": ["A_claim_1"],
    "paper_B_claim_ids": ["B_claim_1"],
    "variables_used": ["variable_name_from_paper_a", "variable_name_from_paper_b"]
  }},

  "proposed_experiment": {{
    "description": "Concrete A/B test description using specific methods and variables from the input JSON.",
    "measurements": ["specific_metric_1", "specific_metric_2"],
    "expected_direction": "increase/decrease"
  }},

  "confidence": "high/medium/low",

  "risk_notes": ["Risk 1", "Risk 2"]
}}

RULES:

1. **Field References**: Use actual values from the input JSON fields (`methods`, `explicit_limitations`, `variables`, `claims`). Do not invent new names.

2. **No New Variables**: You must ONLY use variables present in the `variables` fields from both papers.

3. **Falsifiability**: The hypothesis must be testable with specific measurements (e.g. "Rate of X will decrease by Y%").

4. **Null Result**: If `_confidence_check` is Low, set the hypothesis text to "Insufficient synergy for valid hypothesis."

Return ONLY valid JSON."""
    
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
    
    async def _fix_json_with_groq_async(self, bad_text: str) -> Dict[str, Any]:
        """
        Fix malformed JSON using direct Groq (more reliable than agent for JSON fixing).
        """
        fix_prompt = f"""The following text should be valid JSON but is not. Fix it and return ONLY valid JSON.

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
}}

Return ONLY the JSON object, no commentary."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Fix JSON formatting only. Return ONLY valid JSON."},
                    {"role": "user", "content": fix_prompt}
                ],
                temperature=0.0,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Strip markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)
            
            # Extract JSON if embedded in text
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            return json.loads(content)
        except Exception as e:
            raise RuntimeError(
                f"Failed to fix JSON with Groq.\n"
                f"Error: {e}\n"
                f"Please check your GROQ_API_KEY and network connection."
            ) from e
    
    async def _fix_json_async(self, bad_text: str) -> Dict[str, Any]:
        """
        Fix malformed JSON using SpoonOS Agent (fallback to Groq if agent fails).
        """
        # Try direct Groq first (more reliable for JSON)
        try:
            return await self._fix_json_with_groq_async(bad_text)
        except Exception as groq_error:
            # Fallback to agent if Groq fails
            if not self.spoon_available or not self.spoon_agent:
                raise RuntimeError(
                "SpoonOS is required for JSON fixing.\n"
                "This error occurred while trying to fix malformed JSON from SpoonOS response."
            )
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

        try:
            full_prompt = f"Fix JSON formatting only.\n\n{fix_prompt}"
            response = await self.spoon_agent.run(full_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            return json.loads(content)
        except Exception as e:
            raise RuntimeError(
                f"SpoonOS Agent failed while fixing JSON.\n"
                f"Original error: {e}\n"
                f"Please check your GROQ_API_KEY and network connection."
            ) from e
    
    def _fix_json(self, bad_text: str) -> Dict[str, Any]:
        """
        Fix malformed JSON using SpoonOS Agent (sync version).
        REQUIRES: SpoonOS must be available.
        """
        if not self.spoon_available or not self.spoon_agent:
            raise RuntimeError(
                "SpoonOS is required for JSON fixing.\n"
                "This error occurred while trying to fix malformed JSON from SpoonOS response."
            )
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

        try:
            full_prompt = f"Fix JSON formatting only.\n\n{fix_prompt}"
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need to use async version
                raise RuntimeError(
                    "Cannot use sync _fix_json in async context. Use _fix_json_async instead."
                )
            except RuntimeError as e:
                if "async context" in str(e):
                    raise
                # No event loop, we can use asyncio.run
                response = asyncio.run(self.spoon_agent.run(full_prompt))
                content = response.content if hasattr(response, 'content') else str(response)
                return json.loads(content)
        except Exception as e:
            raise RuntimeError(
                f"SpoonOS Agent failed while fixing JSON.\n"
                f"Original error: {e}\n"
                f"Please check your GROQ_API_KEY and network connection."
            ) from e


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

