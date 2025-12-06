import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load .env 
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file. Please set it in extraction/.env")

client = Groq(api_key=api_key)

MODEL = "llama-3.3-70b-versatile"


def extract_structure(text, title=""):
    """
    Extract structured scientific information from a paper for Trace Phase 1.
    
    This function converts a paper (abstract or full text) into structured JSON
    with claims, methods, evidence, limitations, and variables.
    """

    prompt = f"""
You are extracting structured scientific information from a research paper.

TITLE:
{title}

PAPER TEXT:
{text}

Extract the following fields in STRICT JSON format:

- claims: list of the main scientific claims (all claims)
- methods: the main methods or techniques used
- evidence: concrete evidence supporting the claims (1–2 items, numerical or experimental details if stated)
- explicit_limitations: limitations directly mentioned in the paper
- implicit_limitations: limitations that follow logically from the research
- variables: important variables or scientific factors mentioned (e.g., temperature, pressure, concentration, model parameters)

Return ONLY valid JSON. Do not add commentary.
    """

    response = client.chat.completions.create(
        model=MODEL,
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
        # Remove opening ```json or ```
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {content[:200]}...")
        return fix_json(content)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return fix_json(content)


def fix_json(bad_text):
    """
    Fallback to repair malformed JSON using Groq LLM.
    """
    fix_prompt = f"""
The following text should be valid JSON but is not. Fix it.

TEXT:
{bad_text}

Return only corrected JSON.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Fix JSON formatting only."},
            {"role": "user", "content": fix_prompt}
        ],
        temperature=0.0,
    )

    return json.loads(response.choices[0].message.content)

