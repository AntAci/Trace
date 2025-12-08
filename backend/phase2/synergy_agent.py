"""
Phase 2: Synergy and Conflict Analysis Agent

This module implements a Spoon Agent that compares two Phase 1 structured JSON outputs
and identifies synergies, conflicts, and overlapping variables.

Uses SpoonOS Agent protocol: Agent → SpoonOS → LLM
"""
import json
import os
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load Groq API key (same as Phase 1)
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

# Knowledge graph is dict-based (not Spoon graph objects)
# Spoon graph will be used for workflow orchestration, not knowledge representation

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


class SynergyAgent:
    """
    Spoon Agent for analyzing synergies and conflicts between two papers.
    
    Takes two Phase 1 structured JSON outputs and produces:
    - Overlapping variables
    - Potential synergies
    - Potential conflicts
    - In-memory graph representation
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
    
    async def analyze_async(self, paper_a_json: Dict[str, Any], paper_b_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async version of analyze that properly uses SpoonOS Agent.
        Knowledge graph is dict-based (not Spoon graph objects).
        """
        # Validate inputs
        self._validate_phase1_json(paper_a_json, "Paper A")
        self._validate_phase1_json(paper_b_json, "Paper B")
        
        # Build graph using dict-based representation (knowledge graph stays as dict)
        graph_dict = self._build_graph(paper_a_json, paper_b_json)
        
        # Use SpoonOS to analyze overlaps, synergies, and conflicts
        analysis = await self._analyze_with_spoonos_async(paper_a_json, paper_b_json, graph_dict)
        
        # Enhance graph with overlapping variables and synergy/conflict edges
        final_graph_dict = self._enhance_graph_with_analysis(graph_dict, analysis, paper_a_json, paper_b_json)
        
        # Combine graph and analysis
        result = {
            "overlapping_variables": analysis.get("overlapping_variables", []),
            "potential_synergies": analysis.get("potential_synergies", []),
            "potential_conflicts": analysis.get("potential_conflicts", []),
            "graph": final_graph_dict,
            "graph_engine": "dict"
        }
        
        return result
    
    def analyze(self, paper_a_json: Dict[str, Any], paper_b_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze two papers for synergies and conflicts.
        Knowledge graph is dict-based (not Spoon graph objects).
        """
        # Validate inputs
        self._validate_phase1_json(paper_a_json, "Paper A")
        self._validate_phase1_json(paper_b_json, "Paper B")
        
        # Build graph using dict-based representation (knowledge graph stays as dict)
        graph_dict = self._build_graph(paper_a_json, paper_b_json)
        
        # Use Groq to analyze overlaps, synergies, and conflicts
        analysis = self._analyze_with_groq(paper_a_json, paper_b_json, graph_dict)
        
        # Enhance graph with overlapping variables and synergy/conflict edges
        final_graph_dict = self._enhance_graph_with_analysis(graph_dict, analysis, paper_a_json, paper_b_json)
        
        # Combine graph and analysis
        result = {
            "overlapping_variables": analysis.get("overlapping_variables", []),
            "potential_synergies": analysis.get("potential_synergies", []),
            "potential_conflicts": analysis.get("potential_conflicts", []),
            "graph": final_graph_dict,
            "graph_engine": "dict"
        }
        
        return result
    
    def _validate_phase1_json(self, paper_json: Dict[str, Any], paper_name: str):
        """Validate that input is a valid Phase 1 JSON structure."""
        required_fields = ["claims", "methods", "evidence", "explicit_limitations", 
                          "implicit_limitations", "variables"]
        
        missing_fields = [f for f in required_fields if f not in paper_json]
        if missing_fields:
            raise ValueError(f"{paper_name} missing required fields: {missing_fields}")
    
    def _enhance_graph_with_analysis(self, graph: Dict[str, Any], analysis: Dict[str, Any],
                                    paper_a: Dict[str, Any], paper_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance graph with overlapping variables and synergy/conflict edges.
        
        Adds:
        - Nodes for overlapping variables (marked as "both")
        - Edges for potential synergies
        - Edges for potential conflicts
        """
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        # Add overlapping variable nodes
        for var in analysis.get("overlapping_variables", []):
            var_id = f"var_{var.lower().replace(' ', '_')}"
            # Check if already exists
            if not any(n["id"] == var_id for n in nodes):
                nodes.append({
                    "id": var_id,
                    "type": "variable",
                    "paper": "both",
                    "text": var
                })
        
        # Add edges for synergies
        for synergy in analysis.get("potential_synergies", []):
            synergy_id = synergy.get("id", "")
            paper_a_support = synergy.get("paper_A_support", [])
            paper_b_support = synergy.get("paper_B_support", [])
            
            # Link claims from both papers
            for a_claim in paper_a_support:
                for b_claim in paper_b_support:
                    edges.append({
                        "source": a_claim,
                        "target": b_claim,
                        "relation": "potential_synergy",
                        "synergy_id": synergy_id
                    })
        
        # Add edges for conflicts
        for conflict in analysis.get("potential_conflicts", []):
            conflict_id = conflict.get("id", "")
            paper_a_support = conflict.get("paper_A_support", [])
            paper_b_support = conflict.get("paper_B_support", [])
            
            # Link conflicting claims
            for a_claim in paper_a_support:
                for b_claim in paper_b_support:
                    edges.append({
                        "source": a_claim,
                        "target": b_claim,
                        "relation": "potential_conflict",
                        "conflict_id": conflict_id
                    })
        
        return {"nodes": nodes, "edges": edges}
    
    def _build_graph(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build in-memory graph representation of both papers.
        Creates nodes for claims, variables, and methods, and edges linking them.
        """
        nodes = []
        edges = []
        
        # Add Paper A nodes
        for i, claim in enumerate(paper_a.get("claims", [])):
            node_id = f"A_claim_{i+1}"
            nodes.append({
                "id": node_id,
                "type": "claim",
                "paper": "A",
                "text": claim
            })
        
        for i, var in enumerate(paper_a.get("variables", [])):
            node_id = f"A_var_{i+1}"
            nodes.append({
                "id": node_id,
                "type": "variable",
                "paper": "A",
                "text": str(var)
            })
        
        # Add Paper B nodes
        for i, claim in enumerate(paper_b.get("claims", [])):
            node_id = f"B_claim_{i+1}"
            nodes.append({
                "id": node_id,
                "type": "claim",
                "paper": "B",
                "text": claim
            })
        
        for i, var in enumerate(paper_b.get("variables", [])):
            node_id = f"B_var_{i+1}"
            nodes.append({
                "id": node_id,
                "type": "variable",
                "paper": "B",
                "text": str(var)
            })
        
        # Add edges: claims use variables (within each paper)
        for i, claim in enumerate(paper_a.get("claims", [])):
            claim_id = f"A_claim_{i+1}"
            for j, var in enumerate(paper_a.get("variables", [])):
                var_id = f"A_var_{j+1}"
                edges.append({
                    "source": claim_id,
                    "target": var_id,
                    "relation": "uses_variable"
                })
        
        for i, claim in enumerate(paper_b.get("claims", [])):
            claim_id = f"B_claim_{i+1}"
            for j, var in enumerate(paper_b.get("variables", [])):
                var_id = f"B_var_{j+1}"
                edges.append({
                    "source": claim_id,
                    "target": var_id,
                    "relation": "uses_variable"
                })
        
        return {"nodes": nodes, "edges": edges}
    
    def _analyze_with_groq(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any], 
                          graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use SpoonOS Agent (or Groq fallback) to analyze overlaps, synergies, and conflicts.
        
        Returns structured JSON with:
        - overlapping_variables
        - potential_synergies
        - potential_conflicts
        
        Flow: Agent → SpoonOS → LLM (or direct Groq if SpoonOS unavailable)
        """
        prompt = self._build_analysis_prompt(paper_a, paper_b, graph)
        system_prompt = self._get_system_prompt()
        
        # Use SpoonOS Agent if available
        if self.spoon_available:
            try:
                print("[SpoonOS] Using SpoonOS Agent for analysis (Agent -> SpoonOS -> LLM)")
                # Use SpoonOS Agent to process the request
                full_prompt = f"{system_prompt}\n\n{prompt}"
                # Check if we're in an async context
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, but this is a sync method
                    # We'll use direct Groq for now (async version available)
                    print("[SpoonOS] In async context, using direct Groq (use analyze_async() for SpoonOS)")
                    return self._analyze_with_direct_groq(paper_a, paper_b, graph, prompt, system_prompt)
                except RuntimeError:
                    # No event loop, we can use asyncio.run
                    print("[SpoonOS] Calling SpoonOS Agent.run()...")
                    response = asyncio.run(self.spoon_agent.run(full_prompt))
                    content = response.content if hasattr(response, 'content') else str(response)
                    print("[SpoonOS] Successfully got response from SpoonOS Agent")
            except Exception as e:
                print(f"[Warning] SpoonOS Agent failed: {e}. Falling back to direct Groq.")
                return self._analyze_with_direct_groq(paper_a, paper_b, graph, prompt, system_prompt)
        else:
            print("[Direct Groq] SpoonOS not available, using direct Groq calls")
            return self._analyze_with_direct_groq(paper_a, paper_b, graph, prompt, system_prompt)
    
    async def _analyze_with_spoonos_async(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any], 
                                          graph: Dict[str, Any]) -> Dict[str, Any]:
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
        
        prompt = self._build_analysis_prompt(paper_a, paper_b, graph)
        system_prompt = self._get_system_prompt()
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            print("[SpoonOS] Using SpoonOS Agent for analysis (Agent -> SpoonOS -> LLM)")
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
            raise RuntimeError(
                f"SpoonOS Agent call failed.\n"
                f"Error: {e}\n"
                f"Please check your GROQ_API_KEY and network connection."
            ) from e
        
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
    
    def _analyze_with_direct_groq(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any], 
                                  graph: Dict[str, Any], prompt: str, system_prompt: str) -> Dict[str, Any]:
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
            temperature=0.2,  
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
        """Get the system prompt for the synergy analysis agent."""
        return """You are a scientific analysis agent that compares two structured paper representations.

CRITICAL RULES:
1. You receive ALREADY STRUCTURED JSON from Phase 1 - NOT raw paper text
2. You MUST NOT hallucinate new claims or variables not present in the input JSON
3. You MUST NOT provide generic summarization - only specific cross-paper analysis
4. You MUST return STRICT JSON format only - no free-form paragraphs
5. Only identify synergies/conflicts that are scientifically plausible based on the provided claims, evidence, and variables

Your output must be valid JSON with these exact fields:
- overlapping_variables: list of variable names that appear in both papers
- potential_synergies: list of objects with id, description, paper_A_support, paper_B_support
- potential_conflicts: list of objects with id, description, paper_A_support, paper_B_support

Return ONLY the JSON object, no commentary."""
    
    def _build_analysis_prompt(self, paper_a: Dict[str, Any], paper_b: Dict[str, Any], 
                              graph: Dict[str, Any]) -> str:
        """Build the analysis prompt for Groq."""
        return f"""Analyze these two papers for a "Capability-to-Need" technical fit.

PAPER A: {json.dumps(paper_a, indent=2)}

PAPER B: {json.dumps(paper_b, indent=2)}

Your goal: Find where a specific **method** (from the `methods` field) in one paper addresses a specific **explicit_limitation** (from the `explicit_limitations` field) in the other.

Output a STRICT JSON object:

{{
  "_reasoning_trace": "Briefly explain: Does Paper A have a named method (from methods field) that fixes Paper B's specific limitation (from explicit_limitations field)? Cite the specific method name and limitation name.",

  "potential_synergies": [
    {{
      "id": "syn_1",
      "description": "The [specific method name from methods field] from Paper A addresses the [specific limitation from explicit_limitations field] in Paper B by [technical mechanism explaining how].",
      "paper_A_support": ["A_claim_1", "A_claim_2"],
      "paper_B_support": ["B_claim_1"]
    }}
  ],

  "overlapping_variables": ["variable1", "variable2"],

  "potential_conflicts": [
    {{
      "id": "conf_1",
      "description": "Specific description of the conflict or tension",
      "paper_A_support": ["A_claim_3"],
      "paper_B_support": ["B_claim_1"]
    }}
  ]
}}

CRITICAL RULES:

1. **Field References**: Use actual values from the `methods` and `explicit_limitations` fields in the input JSON. Do not invent new names.

2. **Citation Check**: You CANNOT create a synergy unless you can cite specific claim IDs from BOTH papers (e.g., "A_claim_1", "B_claim_2").

3. **Specificity**: Do not say "Blockchain improves AI". Say "ROCL (from Paper A methods) verifies Agent history (addressing Paper B explicit_limitations)".

4. **Empty Check**: If the `_reasoning_trace` finds no strong technical fit between methods and explicit_limitations, return empty lists.

Return ONLY valid JSON."""
    
    async def _fix_json_async(self, bad_text: str) -> Dict[str, Any]:
        """
        Fix malformed JSON using SpoonOS Agent.
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

Return only corrected JSON with the structure:
{{
  "overlapping_variables": [],
  "potential_synergies": [],
  "potential_conflicts": []
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

Return only corrected JSON with the structure:
{{
  "overlapping_variables": [],
  "potential_synergies": [],
  "potential_conflicts": []
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


def analyze_papers(paper_a_json: Dict[str, Any], paper_b_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze two papers.
    """
    agent = SynergyAgent()
    return agent.analyze(paper_a_json, paper_b_json)


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
    
    result = analyze_papers(paper_a, paper_b)
    print(json.dumps(result, indent=2))

