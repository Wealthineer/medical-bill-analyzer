#!/usr/bin/env python3
"""Test script for BillExtractor (Phase 1.7).

This script tests the complete extraction pipeline using the BillExtractor
orchestrator class.

Usage:
    python scripts/test_bill_extractor.py [path/to/bill.pdf]
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

from medical_bill_analyzer.extraction import BillExtractor, ExtractionStatus
from medical_bill_analyzer.llm.factory import create_llm_provider


def main():
    """Run BillExtractor test."""
    print("=" * 70)
    print("BillExtractor Test - Phase 1.7")
    print("=" * 70)
    print()

    # Load environment variables from .env file
    load_dotenv()

    # Get PDF path from command line or use default
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdf_path = Path("tests/test_data/sample_bills/valid_bill.pdf")

    print(f"PDF: {pdf_path}")

    if not pdf_path.exists():
        print(f"❌ Error: PDF not found at {pdf_path}")
        return 1

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("   Make sure .env file exists with: ANTHROPIC_API_KEY=sk-ant-...")
        return 1

    print(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else "API Key: [set]")
    print()

    # Step 1: Create LLM provider
    print("Step 1: Creating LLM provider...")
    try:
        config = {
            "model": "claude-sonnet-4-20250514",
            "api_key": api_key,
            "max_tokens": 1000,
            "temperature": 0,
        }
        provider = create_llm_provider("anthropic", config)
        print("✅ Anthropic provider created")
        print()
    except Exception as e:
        print(f"❌ Failed to create provider: {e}")
        return 1

    # Step 2: Create BillExtractor
    print("Step 2: Creating BillExtractor...")
    try:
        extractor = BillExtractor(provider)
        print("✅ BillExtractor initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to create extractor: {e}")
        return 1

    # Step 3: Extract from PDF
    print("Step 3: Extracting information from PDF...")
    print("(This orchestrates: validation → text extraction → LLM → validation)")
    print("(May take a few seconds...)")
    print()
    try:
        result = extractor.extract_from_pdf(pdf_path)
        print("✅ Extraction complete")
        print()
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 4: Display results
    print("=" * 70)
    print("EXTRACTION RESULT")
    print("=" * 70)
    print()

    print(f"Status: {result.status.value}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Processable: {result.is_processable}")
    print()

    print(f"PDF Path: {result.pdf_path}")
    print(f"PDF Hash: {result.pdf_hash}")
    print()

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  ❌ {error}")
        print()

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")
        print()

    if result.is_success:
        print("=" * 70)
        print("EXTRACTED DATA")
        print("=" * 70)
        print()
        print(f"Practitioner Name: {result.practitioner_name or 'N/A'}")
        print(f"Practitioner Type: {result.practitioner_type or 'N/A'}")
        print(f"Bill Date: {result.bill_date or 'N/A'}")
        print(f"Bill Number: {result.bill_number or 'N/A'}")
        if result.total_amount:
            print(f"Total Amount: €{result.total_amount:.2f}")
        else:
            print("Total Amount: N/A")
        print(f"Currency: {result.currency or 'N/A'}")
        print()

        print("=" * 70)
        print("RAW EXTRACTED DATA (dict)")
        print("=" * 70)
        print()
        import json
        print(json.dumps(result.extracted_data, indent=2, default=str))
        print()

        print("=" * 70)
        print("SERIALIZED RESULT (to_dict)")
        print("=" * 70)
        print()
        print(json.dumps(result.to_dict(), indent=2, default=str))
        print()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()

    if result.status == ExtractionStatus.SUCCESS:
        print("🎉 SUCCESS! Extraction pipeline working correctly.")
        print()
        print("The BillExtractor successfully:")
        print("  ✅ Validated the PDF")
        print("  ✅ Extracted text from PDF")
        print("  ✅ Sent to Claude for extraction")
        print("  ✅ Validated the extracted data")
        print("  ✅ Returned structured ExtractionResult")
        print()
        print("Ready for Phase 1.8 (Core Business Logic)!")
        return 0
    elif result.status == ExtractionStatus.PDF_INVALID:
        print("⚠️  PDF is invalid or cannot be processed")
        print("   Check the errors above for details")
        return 1
    elif result.status == ExtractionStatus.PDF_NOT_PROCESSABLE:
        print("⚠️  PDF appears to be scanned (no extractable text)")
        print("   The extraction pipeline correctly detected this")
        return 1
    elif result.status == ExtractionStatus.EXTRACTION_FAILED:
        print("⚠️  LLM extraction failed")
        print("   Check API key and connection")
        return 1
    elif result.status == ExtractionStatus.VALIDATION_FAILED:
        print("⚠️  Extracted data failed validation")
        print("   Check the errors and raw data above")
        return 1
    else:
        print(f"⚠️  Unknown status: {result.status}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
