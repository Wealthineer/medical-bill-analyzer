#!/usr/bin/env python3
"""Manual test script for LLM extraction.

This script tests the complete flow:
1. PDF text extraction
2. LLM-based information extraction
3. Response validation

Usage:
    export ANTHROPIC_API_KEY="sk-ant-your-key"
    python scripts/test_llm_extraction.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from medical_bill_analyzer.pdf.extractor import extract_text_from_pdf
from medical_bill_analyzer.llm.factory import create_llm_provider
from medical_bill_analyzer.llm.schemas import BasicExtractionResponse


def main():
    """Run manual LLM extraction test."""
    print("=" * 60)
    print("Medical Bill Analyzer - LLM Extraction Test")
    print("=" * 60)
    print()

    # Configuration
    provider_name = "anthropic"  # Change to "openai" or "ollama" to test others
    pdf_path = Path("tests/test_data/sample_bills/valid_bill.pdf")
    #pdf_path = Path("tests/test_data/sample_bills/ZE-Anteilsrechnung_Plan_11736,11735,11734_ReNr_1_25_68725_3.pdf")

    # Check PDF exists
    if not pdf_path.exists():
        print(f"❌ Error: PDF not found at {pdf_path}")
        print("   Run: python scripts/generate_test_pdfs.py")
        return 1

    # Check API key
    if provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
            print()
            print("Set it with:")
            print("  export ANTHROPIC_API_KEY='sk-ant-your-key-here'")
            return 1
        config = {
            "model": "claude-sonnet-4-20250514",
            "api_key": api_key,
            "max_tokens": 1000,
            "temperature": 0,
        }
    elif provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Error: OPENAI_API_KEY environment variable not set")
            return 1
        config = {
            "model": "gpt-4o-mini",
            "api_key": api_key,
            "max_tokens": 1000,
            "temperature": 0,
        }
    else:  # ollama
        config = {
            "model": "llama3.1:8b",
            "host": "http://localhost:11434",
        }

    print(f"Provider: {provider_name}")
    print(f"PDF: {pdf_path}")
    print()

    # Step 1: Extract text from PDF
    print("Step 1: Extracting text from PDF...")
    try:
        text = extract_text_from_pdf(pdf_path)
        print(f"✅ Extracted {len(text)} characters")
        print()
        print("First 200 characters:")
        print("-" * 60)
        print(text[:200])
        print("-" * 60)
        print()
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        return 1

    # Step 2: Create LLM provider
    print("Step 2: Initializing LLM provider...")
    try:
        provider = create_llm_provider(provider_name, config)
        print(f"✅ {provider_name.title()} provider ready")
        print()
    except Exception as e:
        print(f"❌ Provider initialization failed: {e}")
        return 1

    # Step 3: Test connection
    print("Step 3: Testing API connection...")
    try:
        if provider.test_connection():
            print("✅ Connection successful")
            print()
        else:
            print("❌ Connection test failed")
            return 1
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return 1

    # Step 4: Extract information
    print("Step 4: Extracting information with LLM...")
    print("(This may take a few seconds...)")
    try:
        result_dict = provider.extract(text)
        print("✅ Extraction successful")
        print()
        print("Raw response:")
        print("-" * 60)
        import json
        print(json.dumps(result_dict, indent=2, ensure_ascii=False))
        print("-" * 60)
        print()
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 5: Validate response
    print("Step 5: Validating extracted data...")
    try:
        response = BasicExtractionResponse(**result_dict)
        print("✅ Validation successful")
        print()
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 6: Display results
    print("=" * 60)
    print("EXTRACTED INFORMATION")
    print("=" * 60)
    print(f"Practitioner Name: {response.practitioner_name or 'N/A'}")
    print(f"Practitioner Type: {response.practitioner_type or 'N/A'}")
    print(f"Bill Date: {response.bill_date or 'N/A'}")
    print(f"Bill Number: {response.bill_number or 'N/A'}")
    print(f"Total Amount: €{response.total_amount:.2f}" if response.total_amount else "Total Amount: N/A")
    print(f"Currency: {response.currency}")
    print("=" * 60)
    print()

    # Verify expected values for test PDF
    print("Verification (comparing to expected values):")
    expected = {
        "practitioner_name": "Dr. med. Anna Müller",
        "practitioner_type": "Arzt",
        "bill_number": "2024-001234",
        "total_amount": 29.49,
    }

    all_match = True
    for field, expected_value in expected.items():
        actual_value = getattr(response, field)
        if actual_value == expected_value:
            print(f"  ✅ {field}: {actual_value}")
        else:
            print(f"  ⚠️  {field}: got {actual_value}, expected {expected_value}")
            all_match = False

    print()
    if all_match:
        print("🎉 All fields match expected values!")
        print("   LLM extraction is working correctly.")
    else:
        print("⚠️  Some fields don't match expected values.")
        print("   This may indicate the prompt needs adjustment.")

    print()
    print("Test completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
