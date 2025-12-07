import os
import json
import asyncio
from dotenv import load_dotenv

# Load .env 
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path)

# Try to import SpoonOS LLM components
try:
    from spoon_ai.llm import LLMManager, ConfigurationManager
    from spoon_ai.chat import ChatBot
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

# Initialize SpoonOS LLM if available
llm_manager = None
chatbot = None
if SPOON_AVAILABLE:
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            # Use OpenAI provider with Groq's base URL (OpenAI-compatible API)
            # Groq API endpoint: https://api.groq.com/openai/v1
            try:
                print("[SpoonOS] Configuring ChatBot with OpenAI provider -> Groq base URL")
                chatbot = ChatBot(
                    llm_provider="openai",
                    model_name="llama-3.3-70b-versatile",
                    api_key=api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                print("[SpoonOS] Successfully created ChatBot with Groq via OpenAI provider")
            except Exception as e1:
                print(f"[Warning] Failed to create ChatBot with OpenAI->Groq: {e1}")
                # Try LLMManager as fallback
                try:
                    config_manager = ConfigurationManager()
                    llm_manager = LLMManager(config_manager)
                    chatbot = llm_manager
                except Exception as e2:
                    print(f"[Warning] Failed to create LLMManager: {e2}")
                    chatbot = None
    except Exception as e:
        print(f"[Warning] Failed to initialize SpoonOS LLM: {e}")
        print("Falling back to direct Groq calls.")
        SPOON_AVAILABLE = False
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            client = Groq(api_key=api_key)
        MODEL = "llama-3.3-70b-versatile"


async def extract_structure_async(text, title=""):
    """
    Extract structured scientific information from a paper for Trace Phase 1.
    
    This function converts a paper (abstract or full text) into structured JSON
    with claims, methods, evidence, limitations, and variables.
    
    Uses SpoonOS LLM protocol layer (Tool → SpoonOS → LLM).
    
    REQUIRES: SpoonOS must be installed and properly configured.
    Raises RuntimeError if SpoonOS is unavailable.
    """
    # STRICT REQUIREMENT: SpoonOS must be available
    if not SPOON_AVAILABLE:
        raise RuntimeError(
            "SpoonOS is REQUIRED for this project.\n"
            "Install with: pip install spoon-ai-sdk\n"
            "Ensure GROQ_API_KEY is set in extraction/.env"
        )
    
    if not chatbot and not llm_manager:
        raise RuntimeError(
            "SpoonOS ChatBot or LLMManager must be initialized.\n"
            "Check that GROQ_API_KEY is set in extraction/.env\n"
            "SpoonOS initialization may have failed during import."
        )
    
    prompt = f"""
You are a Precision Scientific Entity Extractor.

TITLE: {title}

PAPER TEXT: {text}

INSTRUCTIONS:

1. First, scan the text for specific named entities (algorithms, metrics, specific errors).

2. List these in the `_analysis_scratchpad` to verify they exist in the text.

3. Then, categorize them into the strict fields below.

Output a STRICT JSON object:

{{
  "_analysis_scratchpad": "List 3-5 specific technical terms or numbers found in the text (e.g. 'ROCL', 'p < 0.05') before categorizing.",

  "claims": ["Claim 1", "Claim 2"],

  "methods": ["Specific Named Algorithm 1", "Protocol 2"],

  "evidence": ["Quantitative Metric 1", "Experimental Result 2"],

  "explicit_limitations": ["Specific Failure Mode 1", "Error 2"],

  "implicit_limitations": ["Logical Risk 1"],

  "variables": ["Input Parameter 1", "Factor 2"]
}}

CRITICAL RULES:

- **methods**: Must be CAPITALIZED, named algorithms, architectures, or protocols (e.g., "ROCL", "DeepLabCut", "Transformer").

- **explicit_limitations**: Must be specific failure modes or reliability problems (e.g., "hallucination", "latency", "mode collapse").

- **evidence**: Must be specific numbers, percentages, or statistical results.

- **Escape Hatch**: If a field has no specific named entities, return an empty list [].

Return ONLY valid JSON.
    """

    # Use SpoonOS ChatBot (primary) or LLMManager (fallback)
    if chatbot:
        try:
            print("[SpoonOS Phase 1] Using SpoonOS ChatBot for extraction (Tool -> SpoonOS -> LLM)")
            response = await chatbot.chat([
                {"role": "system", "content": "Return STRICT JSON only."},
                {"role": "user", "content": prompt}
            ])
            content = response.content if hasattr(response, 'content') else str(response)
            print("[SpoonOS Phase 1] Successfully got response from SpoonOS ChatBot")
        except Exception as e:
            # Try LLMManager if ChatBot fails
            if llm_manager:
                print(f"[Warning] SpoonOS ChatBot failed: {e}. Trying LLMManager...")
                try:
                    response = await llm_manager.chat([
                        {"role": "system", "content": "Return STRICT JSON only."},
                        {"role": "user", "content": prompt}
                    ])
                    content = response.content if hasattr(response, 'content') else str(response)
                    print("[SpoonOS Phase 1] Successfully got response from SpoonOS LLMManager")
                except Exception as e2:
                    raise RuntimeError(
                        f"SpoonOS call failed (both ChatBot and LLMManager failed).\n"
                        f"ChatBot error: {e}\n"
                        f"LLMManager error: {e2}\n"
                        f"Please check your GROQ_API_KEY and network connection."
                    ) from e2
            else:
                raise RuntimeError(
                    f"SpoonOS ChatBot failed and LLMManager is not available.\n"
                    f"Error: {e}\n"
                    f"Please check your GROQ_API_KEY and network connection."
                ) from e
    elif llm_manager:
        try:
            print("[SpoonOS Phase 1] Using SpoonOS LLMManager for extraction (Tool -> SpoonOS -> LLM)")
            response = await llm_manager.chat([
                {"role": "system", "content": "Return STRICT JSON only."},
                {"role": "user", "content": prompt}
            ])
            content = response.content if hasattr(response, 'content') else str(response)
            print("[SpoonOS Phase 1] Successfully got response from SpoonOS LLMManager")
        except Exception as e:
            raise RuntimeError(
                f"SpoonOS LLMManager call failed.\n"
                f"Error: {e}\n"
                f"Please check your GROQ_API_KEY and network connection."
            ) from e
    else:
        raise RuntimeError(
            "SpoonOS ChatBot and LLMManager are both unavailable.\n"
            "SpoonOS initialization may have failed. Check your configuration."
        )
    
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
        print(f"Response content: {content[:200]}...")
        return await fix_json_async(content)


def extract_structure(text, title=""):
    """
    Synchronous wrapper for extract_structure_async.
    """
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, need to use a different approach
        # For now, just use the direct Groq fallback in sync mode
        return _extract_with_groq(text, title)
    except RuntimeError:
        # No event loop running, we can use asyncio.run
        try:
            return asyncio.run(extract_structure_async(text, title))
        except Exception as e:
            print(f"[Warning] Async extraction failed: {e}. Using direct Groq.")
            return _extract_with_groq(text, title)


# Global variables for Groq fallback
_groq_client = None
_groq_model = "llama-3.3-70b-versatile"

def _get_groq_client():
    """Get or create Groq client for fallback."""
    global _groq_client, _groq_model
    if _groq_client is None:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file. Please set it in extraction/.env")
        _groq_client = Groq(api_key=api_key)
    return _groq_client, _groq_model

def _extract_with_groq(text, title=""):
    """
    Fallback function using direct Groq calls (for when SpoonOS is not available).
    """
    client, model = _get_groq_client()
    
    prompt = f"""
You are extracting structured scientific information from a research paper.

TITLE: {title}

PAPER TEXT: {text}

INSTRUCTIONS:

1. First, scan the text for specific named entities (algorithms, metrics, specific errors).

2. List these in the `_analysis_scratchpad` to verify they exist in the text.

3. Then, categorize them into the strict fields below.

Output a STRICT JSON object:

{{
  "_analysis_scratchpad": "List 3-5 specific technical terms or numbers found in the text (e.g. 'ROCL', 'p < 0.05') before categorizing.",

  "claims": ["Claim 1", "Claim 2"],

  "methods": ["Specific Named Algorithm 1", "Protocol 2"],

  "evidence": ["Quantitative Metric 1", "Experimental Result 2"],

  "explicit_limitations": ["Specific Failure Mode 1", "Error 2"],

  "implicit_limitations": ["Logical Risk 1"],

  "variables": ["Input Parameter 1", "Factor 2"]
}}

CRITICAL RULES:

- **methods**: Must be CAPITALIZED, named algorithms, architectures, or protocols (e.g., "ROCL", "DeepLabCut", "Transformer").

- **explicit_limitations**: Must be specific failure modes or reliability problems (e.g., "hallucination", "latency", "mode collapse").

- **evidence**: Must be specific numbers, percentages, or statistical results.

- **Escape Hatch**: If a field has no specific named entities, return an empty list [].

Return ONLY valid JSON.
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return STRICT JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
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
        print(f"Response content: {content[:200]}...")
        # Use async fix_json
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, fix_json_async(content))
                    return future.result()
            else:
                return loop.run_until_complete(fix_json_async(content))
        except RuntimeError:
            return asyncio.run(fix_json_async(content))


async def fix_json_async(bad_text):
    """
    Fallback to repair malformed JSON using SpoonOS LLM (or Groq if not available).
    """
    fix_prompt = f"""
The following text should be valid JSON but is not. Fix it.

TEXT:
{bad_text}

Return only corrected JSON.
    """

    # Use SpoonOS if available
    if SPOON_AVAILABLE and chatbot:
        try:
            response = await chatbot.chat([
                {"role": "system", "content": "Fix JSON formatting only."},
                {"role": "user", "content": fix_prompt}
            ])
            content = response.content if hasattr(response, 'content') else str(response)
            return json.loads(content)
        except Exception as e:
            print(f"[Warning] SpoonOS ChatBot failed in fix_json: {e}")
            if llm_manager:
                try:
                    response = await llm_manager.chat([
                        {"role": "system", "content": "Fix JSON formatting only."},
                        {"role": "user", "content": fix_prompt}
                    ])
                    content = response.content if hasattr(response, 'content') else str(response)
                    return json.loads(content)
                except:
                    pass
    
    # Fallback to direct Groq
    client, model = _get_groq_client()
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Fix JSON formatting only."},
            {"role": "user", "content": fix_prompt}
        ],
        temperature=0.0,
    )
    return json.loads(response.choices[0].message.content)

