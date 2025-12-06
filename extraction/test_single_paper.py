"""
Test extraction on a single paper.
You can either provide a JSON file or use a sample paper.
"""
import json
import sys
from extract_groq import extract_structure

def test_from_file(filename):
    """Test extraction from a JSON file."""
    print(f"\n[Test] Loading paper from {filename}")
    
    with open(filename, "r", encoding="utf-8") as f:
        paper = json.load(f)
    
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    
    if not abstract:
        print("[ERROR] No abstract found in paper file")
        return
    
    print(f"[Test] Title: {title[:80]}...")
    print(f"[Test] Abstract length: {len(abstract)} characters")
    print("\n[Test] Extracting structure...")
    print("=" * 60)
    
    try:
        structured = extract_structure(abstract, title)
        
        print("\n[SUCCESS] Extraction complete!")
        print("\nExtracted structure:")
        print("-" * 60)
        print(json.dumps(structured, indent=2))
        
        # Save to extracted directory
        import os
        os.makedirs("extracted", exist_ok=True)
        output_file = f"extracted/test_paper_structured.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured, f, indent=2)
        
        print(f"\n[SUCCESS] Saved to {output_file}")
        
    except Exception as e:
        print(f"\n[ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()

def test_sample_paper():
    """Test with a sample paper."""
    sample_paper = {
        "title": "Attention Is All You Need: Transformer Architecture for Neural Machine Translation",
        "abstract": """
        The dominant sequence transduction models are based on complex recurrent or convolutional 
        neural networks that include an encoder and a decoder. The best performing models also 
        connect the encoder and decoder through an attention mechanism. We propose a new simple 
        network architecture, the Transformer, based solely on attention mechanisms, dispensing 
        with recurrence and convolutions entirely. Experiments on two machine translation tasks 
        show that these models are superior in quality while being more parallelizable and 
        requiring significantly less time to train. Our model achieves 28.4 BLEU on the 
        WMT 2014 English-to-German translation task, improving over the existing best results, 
        including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, 
        our model establishes a new single-model state-of-the-art BLEU score of 41.8 after 
        training for 3.5 days on eight GPUs, a small fraction of the training costs of the 
        best models from the literature. We show that the Transformer generalizes well to 
        other tasks by applying it successfully to large-scale constituency parsing with 
        large and limited training data.
        """
    }
    
    print("\n[Test] Using sample paper (Transformer architecture)")
    print("=" * 60)
    
    title = sample_paper["title"]
    abstract = sample_paper["abstract"].strip()
    
    print(f"[Test] Title: {title}")
    print(f"[Test] Abstract length: {len(abstract)} characters")
    print("\n[Test] Extracting structure...")
    print("=" * 60)
    
    try:
        structured = extract_structure(abstract, title)
        
        print("\n[SUCCESS] Extraction complete!")
        print("\nExtracted structure:")
        print("-" * 60)
        print(json.dumps(structured, indent=2))
        
        # Save to extracted directory
        import os
        os.makedirs("extracted", exist_ok=True)
        output_file = "extracted/sample_paper_structured.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured, f, indent=2)
        
        print(f"\n[SUCCESS] Saved to {output_file}")
        
    except Exception as e:
        print(f"\n[ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with provided file
        test_from_file(sys.argv[1])
    else:
        # Test with sample paper
        test_sample_paper()

