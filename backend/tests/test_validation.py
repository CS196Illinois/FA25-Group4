"""Quick test to verify the enhanced ticker validation system."""
import sys
import os

# Add parent directory to path to import Product modules


from core.cleaner import clean_company_and_ticker

print("Testing Enhanced Ticker Validation System")
print("=" * 60)

# Test 1: Well-known company (should have high confidence and validate)
print("\n[Test 1: Well-known company - Apple]")
result = clean_company_and_ticker("Apple")
print(f"Result: {result}")
print(f"  Company: {result['company']}")
print(f"  Ticker: {result['ticker']}")
print(f"  Confidence: {result['confidence']}%")
print(f"  Needs Confirmation: {result['needs_confirmation']}")

# Test 2: Lesser-known company (may need confirmation)
print("\n[Test 2: Lesser-known company - Richtech]")
result = clean_company_and_ticker("Richtech")
print(f"Result: {result}")
print(f"  Company: {result['company']}")
print(f"  Ticker: {result['ticker']}")
print(f"  Confidence: {result['confidence']}%")
print(f"  Needs Confirmation: {result['needs_confirmation']}")
if result.get('candidates'):
    print(f"  Candidates: {len(result['candidates'])}")
    for i, cand in enumerate(result['candidates'], 1):
        print(f"    {i}. {cand['company']} ({cand['ticker']})")

# Test 3: Ticker symbol input (should validate easily)
print("\n[Test 3: Ticker symbol - MSFT]")
result = clean_company_and_ticker("MSFT")
print(f"Result: {result}")
print(f"  Company: {result['company']}")
print(f"  Ticker: {result['ticker']}")
print(f"  Confidence: {result['confidence']}%")
print(f"  Needs Confirmation: {result['needs_confirmation']}")

print("\n" + "=" * 60)
print("Test completed!")
