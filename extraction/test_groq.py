"""
Quick test script to verify Groq API connection and extraction function.
"""
import os
from extract_groq import extract_structure

# Test with a sample abstract
test_title = "Machine Learning for Scientific Discovery"
test_abstract = """
We present a novel approach to scientific discovery using machine learning.
Our method achieves 95% accuracy on benchmark datasets. However, the approach
is limited to structured data and may not generalize to other domains.
We evaluate on three datasets: DatasetA, DatasetB, and DatasetC.
"""

print("Testing Groq API connection...")
print("=" * 50)

try:
    result = extract_structure(test_abstract, test_title)
    print("\n[SUCCESS] Extraction successful!")
    print("\nExtracted structure:")
    print("-" * 50)
    
    import json
    print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Test passed! Your API key is working correctly.")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    print("\nPlease check:")
    print("1. Your GROQ_API_KEY is set in extraction/.env")
    print("2. The API key is valid")
    print("3. You have internet connection")

