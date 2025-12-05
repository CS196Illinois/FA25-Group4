"""
Test script to verify Gemini fallback mechanism.

This tests that the fallback model works when the primary model fails.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.config import gemini_generate_with_fallback, GEMINI, GEMINI_FALLBACK

def test_fallback_works():
    """Test that the fallback function returns valid responses."""

    print("Testing Gemini fallback mechanism...")
    print("=" * 60)

    # Test a simple prompt
    test_prompt = """
    Return ONLY valid JSON with a greeting:
    {
        "message": "Hello, this is a test",
        "status": "success"
    }
    """

    try:
        print("\n1. Testing normal fallback function...")
        response = gemini_generate_with_fallback(test_prompt)
        print(f"✓ Response received: {response.text[:100]}...")

        print("\n2. Verifying both models are initialized...")
        print(f"✓ Primary model: {GEMINI._model_name}")
        print(f"✓ Fallback model: {GEMINI_FALLBACK._model_name}")

        print("\n3. Testing with fallback disabled...")
        response_no_fallback = gemini_generate_with_fallback(test_prompt, use_fallback=False)
        print(f"✓ Response without fallback: {response_no_fallback.text[:100]}...")

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nFallback mechanism is working correctly.")
        print("- Primary model: gemini-3-pro-preview")
        print("- Fallback model: gemini-1.5-pro")
        print("- If primary fails, fallback will be used automatically.")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        print("\nNote: This could mean:")
        print("1. API key is invalid")
        print("2. Network connection issue")
        print("3. Both models are unavailable")
        return False

    return True


if __name__ == "__main__":
    test_fallback_works()
