"""
FastAPI Server for Trace Pipeline

Exposes the Trace pipeline as a REST API for the web frontend.
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from process_papers import process_papers_from_folder
from extraction.pdf_reader import extract_text_from_pdf, extract_title_from_pdf
from extraction.spoon_tool import extract_paper_structure_async
from phase2.synergy_agent import SynergyAgent
from phase3.hypothesis_agent import HypothesisAgent
from phase4.minting_service import mint_hypothesis

app = FastAPI(title="Trace API", version="1.0.0")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PaperInput(BaseModel):
    """Input model for paper text content"""
    title: str
    content: str


class ProcessRequest(BaseModel):
    """Request model for processing papers"""
    paper_a: PaperInput
    paper_b: PaperInput
    author_wallet: Optional[str] = "NXXXX..."
    use_neofs: bool = True
    use_x402: bool = False


def transform_backend_to_frontend(backend_result: Dict[str, Any], paper_a_input: PaperInput, paper_b_input: PaperInput) -> Dict[str, Any]:
    """
    Transform backend pipeline result to frontend HypothesisArtifact format.
    
    Args:
        backend_result: Result from process_papers_from_folder
        paper_a_input: Original paper A input
        paper_b_input: Original paper B input
        
    Returns:
        Frontend-compatible HypothesisArtifact dict
    """
    hypothesis_card = backend_result.get("hypothesis", {})
    mint_result = backend_result.get("mint_result", {})
    paper_a_json = backend_result.get("paper_a", {})
    paper_b_json = backend_result.get("paper_b", {})
    
    # Extract confidence scores (backend uses string, frontend needs numbers)
    confidence_str = hypothesis_card.get("confidence", "medium")
    confidence_map = {
        "high": {"overall": 85, "novelty": 80, "plausibility": 90, "testability": 85},
        "medium": {"overall": 65, "novelty": 60, "plausibility": 70, "testability": 65},
        "low": {"overall": 45, "novelty": 40, "plausibility": 50, "testability": 45},
    }
    confidence = confidence_map.get(confidence_str.lower(), confidence_map["medium"])
    
    # Transform evidence from backend format to frontend format
    evidence = []
    source_support = hypothesis_card.get("source_support", {})
    paper_a_claims = paper_a_json.get("claims", [])
    paper_b_claims = paper_b_json.get("claims", [])
    
    # Map claim IDs to actual claims
    # Handle different claim formats: dict with claim_id, or string, or dict with different keys
    claim_map = {}
    
    # Process Paper A claims
    for idx, claim in enumerate(paper_a_claims):
        if isinstance(claim, dict):
            # Try different possible keys for claim ID
            claim_id = claim.get("claim_id") or claim.get("id") or str(idx + 1)
            claim_text = claim.get("claim_text") or claim.get("text") or claim.get("claim") or str(claim)
            claim_map[f"A_claim_{claim_id}"] = {"claim_id": claim_id, "claim_text": claim_text}
        elif isinstance(claim, str):
            # Claim is just a string
            claim_map[f"A_claim_{idx + 1}"] = {"claim_id": str(idx + 1), "claim_text": claim}
        else:
            # Fallback
            claim_map[f"A_claim_{idx + 1}"] = {"claim_id": str(idx + 1), "claim_text": str(claim)}
    
    # Process Paper B claims
    for idx, claim in enumerate(paper_b_claims):
        if isinstance(claim, dict):
            claim_id = claim.get("claim_id") or claim.get("id") or str(idx + 1)
            claim_text = claim.get("claim_text") or claim.get("text") or claim.get("claim") or str(claim)
            claim_map[f"B_claim_{claim_id}"] = {"claim_id": claim_id, "claim_text": claim_text}
        elif isinstance(claim, str):
            claim_map[f"B_claim_{idx + 1}"] = {"claim_id": str(idx + 1), "claim_text": claim}
        else:
            claim_map[f"B_claim_{idx + 1}"] = {"claim_id": str(idx + 1), "claim_text": str(claim)}
    
    # Build evidence array - try to match claim IDs from source_support
    for claim_id in source_support.get("paper_A_claim_ids", []):
        claim = claim_map.get(claim_id, {})
        if isinstance(claim, dict):
            quote = claim.get("claim_text", "")[:200] or "Relevant finding from paper"
        else:
            quote = str(claim)[:200] if claim else "Relevant finding from paper"
        
        evidence.append({
            "paper": paper_a_input.title,
            "page": 1,  # Backend doesn't track page numbers
            "quote": quote,
            "confidenceLevel": "High" if confidence_str == "high" else "Medium"
        })
    
    for claim_id in source_support.get("paper_B_claim_ids", []):
        claim = claim_map.get(claim_id, {})
        if isinstance(claim, dict):
            quote = claim.get("claim_text", "")[:200] or "Relevant finding from paper"
        else:
            quote = str(claim)[:200] if claim else "Relevant finding from paper"
        
        evidence.append({
            "paper": paper_b_input.title,
            "page": 1,
            "quote": quote,
            "confidenceLevel": "High" if confidence_str == "high" else "Medium"
        })
    
    # If no evidence was found, add placeholder evidence
    if not evidence:
        evidence.append({
            "paper": paper_a_input.title,
            "page": 1,
            "quote": "Evidence from paper analysis",
            "confidenceLevel": "Medium"
        })
        evidence.append({
            "paper": paper_b_input.title,
            "page": 1,
            "quote": "Evidence from paper analysis",
            "confidenceLevel": "Medium"
        })
    
    # Transform proposed experiment
    proposed_exp = hypothesis_card.get("proposed_experiment", {})
    procedure = proposed_exp.get("description", "").split(". ") if proposed_exp.get("description") else []
    if procedure and not procedure[-1].endswith("."):
        procedure[-1] += "."
    
    # Build novelty assessment
    novelty_assessment = {
        "isNovel": confidence.get("novelty", 50) > 60,
        "reasoning": hypothesis_card.get("rationale", "Based on synergy analysis between the two papers.")
    }
    
    # Extract hypothesis ID from mint result or generate
    hypothesis_id = mint_result.get("hypothesis_id") or hypothesis_card.get("hypothesis_id", "unknown")
    numeric_id = int(hypothesis_id.split("_")[-1][:3], 16) if "_" in hypothesis_id else 100
    
    # Build blockchain info
    blockchain = None
    if mint_result.get("neo_tx_id"):
        blockchain = {
            "network": "Neo N3",
            "transactionHash": mint_result.get("neo_tx_id", ""),
            "nftId": numeric_id,
            "explorerUrl": f"https://neoscan.io/transaction/{mint_result.get('neo_tx_id', '')}",
            "blockNumber": 1240592  # Mock block number
        }
    
    # Build source papers array
    source_papers = [
        {
            "id": "paper_a",
            "title": paper_a_input.title,
            "authors": paper_a_json.get("authors", "Unknown"),
            "year": paper_a_json.get("year", 2024),
            "content": paper_a_input.content[:500],  # Truncate for frontend
            "fileName": None
        },
        {
            "id": "paper_b",
            "title": paper_b_input.title,
            "authors": paper_b_json.get("authors", "Unknown"),
            "year": paper_b_json.get("year", 2024),
            "content": paper_b_input.content[:500],
            "fileName": None
        }
    ]
    
    # Build final artifact
    artifact = {
        "id": numeric_id,
        "timestamp": hypothesis_card.get("created_at", mint_result.get("created_at", "")),
        "title": hypothesis_card.get("hypothesis", "")[:100] or "Generated Hypothesis",
        "statement": hypothesis_card.get("hypothesis", ""),
        "summary": hypothesis_card.get("rationale", ""),
        "confidence": confidence,
        "evidence": evidence[:4],  # Limit to 4 items
        "noveltyAssessment": novelty_assessment,
        "proposedExperiment": {
            "procedure": procedure if procedure else ["Experimental setup to be determined."],
            "expectedOutcome": proposed_exp.get("expected_direction", "positive") or "positive"
        },
        "sourcePapers": source_papers,
    }
    
    if blockchain:
        artifact["blockchain"] = blockchain
    
    return artifact


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Trace API", "version": "1.0.0"}


async def process_papers_from_text(
    paper_a_text: str,
    paper_a_title: str,
    paper_b_text: str,
    paper_b_title: str,
    author_wallet: str = "NXXXX...",
    use_neofs: bool = True,
    use_x402: bool = False
) -> Dict[str, Any]:
    """
    Process papers from text content directly (bypasses PDF reading).
    """
    import json
    
    try:
        # Phase 1: Extract paper structures
        paper_a_json_str = await extract_paper_structure_async(
            paper_text=paper_a_text,
            title=paper_a_title
        )
        paper_b_json_str = await extract_paper_structure_async(
            paper_text=paper_b_text,
            title=paper_b_title
        )
        
        paper_a_json = json.loads(paper_a_json_str)
        paper_b_json = json.loads(paper_b_json_str)
        
        if "error" in paper_a_json:
            raise ValueError(f"Paper A extraction error: {paper_a_json['error']}")
        if "error" in paper_b_json:
            raise ValueError(f"Paper B extraction error: {paper_b_json['error']}")
        
        # Phase 2: Analyze synergies
        agent = SynergyAgent()
        synergy_json = await agent.analyze_async(paper_a_json, paper_b_json)
        
        # Phase 3: Generate hypothesis
        hypothesis_agent = HypothesisAgent()
        hypothesis_card = await hypothesis_agent.generate_hypothesis_async(
            paper_a_json, paper_b_json, synergy_json
        )
        
        # Phase 4: Mint hypothesis
        mint_result = await asyncio.to_thread(
            mint_hypothesis,
            card=hypothesis_card,
            author_wallet=author_wallet,
            use_neofs=use_neofs,
            use_x402=use_x402
        )
        
        return {
            "paper_a": paper_a_json,
            "paper_b": paper_b_json,
            "synergy_analysis": synergy_json,
            "hypothesis": hypothesis_card,
            "mint_result": mint_result
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/process-papers")
async def process_papers_endpoint(request: ProcessRequest):
    """
    Process two papers and generate a hypothesis.
    
    Accepts paper text content directly (for frontend compatibility).
    """
    try:
        # Process papers from text directly
        result = await process_papers_from_text(
            paper_a_text=request.paper_a.content,
            paper_a_title=request.paper_a.title,
            paper_b_text=request.paper_b.content,
            paper_b_title=request.paper_b.title,
            author_wallet=request.author_wallet,
            use_neofs=request.use_neofs,
            use_x402=request.use_x402
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Transform to frontend format
        artifact = transform_backend_to_frontend(result, request.paper_a, request.paper_b)
        
        return JSONResponse(content=artifact)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/process-pdfs")
async def process_pdfs_endpoint(
    paper_a: UploadFile = File(...),
    paper_b: UploadFile = File(...),
    author_wallet: str = Form("NXXXX..."),
    use_neofs: bool = Form(True),
    use_x402: bool = Form(False)
):
    """
    Process two PDF files and generate a hypothesis.
    """
    try:
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save uploaded PDFs
            paper_a_path = os.path.join(temp_dir, paper_a.filename or "paper_a.pdf")
            paper_b_path = os.path.join(temp_dir, paper_b.filename or "paper_b.pdf")
            
            with open(paper_a_path, "wb") as f:
                f.write(await paper_a.read())
            
            with open(paper_b_path, "wb") as f:
                f.write(await paper_b.read())
            
            # Process through pipeline
            result = await process_papers_from_folder(
                input_folder=temp_dir,
                author_wallet=author_wallet,
                use_neofs=use_neofs,
                use_x402=use_x402
            )
            
            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])
            
            # Extract paper titles from result
            paper_a_title = result.get("paper_a", {}).get("title", "Paper A")
            paper_b_title = result.get("paper_b", {}).get("title", "Paper B")
            
            # Read paper texts for frontend
            paper_a_text = extract_text_from_pdf(paper_a_path)
            paper_b_text = extract_text_from_pdf(paper_b_path)
            
            paper_a_input = PaperInput(title=paper_a_title, content=paper_a_text[:5000])
            paper_b_input = PaperInput(title=paper_b_title, content=paper_b_text[:5000])
            
            # Transform to frontend format
            artifact = transform_backend_to_frontend(result, paper_a_input, paper_b_input)
            
            return JSONResponse(content=artifact)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

