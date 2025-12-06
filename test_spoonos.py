"""
Test script to verify SpoonOS integration with Groq via OpenAI provider.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv("extraction/.env")

async def test_spoonos():
    """Test SpoonOS Agent with Groq via OpenAI provider."""
    print("=" * 60)
    print("Testing SpoonOS Integration")
    print("=" * 60)
    
    try:
        from spoon_ai.agents import SpoonReactAI
        from spoon_ai.chat import ChatBot
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[ERROR] GROQ_API_KEY not found in extraction/.env")
            return False
        
        print("\n[Step 1] Creating ChatBot with OpenAI provider -> Groq base URL...")
        chatbot = ChatBot(
            llm_provider="openai",
            model_name="llama-3.3-70b-versatile",
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        print("[OK] ChatBot created successfully")
        
        print("\n[Step 2] Creating SpoonOS Agent...")
        agent = SpoonReactAI(llm=chatbot)
        print("[OK] SpoonOS Agent created successfully")
        
        print("\n[Step 3] Testing Agent -> SpoonOS -> LLM flow...")
        print("Sending test prompt: 'What is 2+2? Answer in one word.'")
        
        response = await agent.run("What is 2+2? Answer in one word.")
        
        content = response.content if hasattr(response, 'content') else str(response)
        print(f"[OK] Got response from SpoonOS Agent: {content}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] SpoonOS is working correctly!")
        print("Flow: Agent -> SpoonOS -> LLM (Groq via OpenAI provider)")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_spoonos())
    exit(0 if result else 1)

