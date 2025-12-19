# Manual Testing Guide

**NOTE: This file is outdated. Phase 1.9 is now complete!**

For current testing instructions, see **[TESTING_GUIDE.md](TESTING_GUIDE.md)** which provides step-by-step instructions for testing the complete CLI application.

---

## Current Status (Phase 1.9 Complete)

✅ **Fully Implemented:**
- Configuration management
- Database layer (SQLite)
- PDF text extraction
- LLM provider abstraction (Anthropic, OpenAI, Ollama)
- Information extraction pipeline
- Core business logic (BillProcessor, BonusCalculator)
- **CLI commands (setup, add, list, total, bonus-check)**

## Quick Start

Instead of manual Python testing, you can now use the complete CLI:

### 1. Run Setup Wizard
```bash
python -m medical_bill_analyzer setup
```

This will guide you through:
- LLM provider selection
- API key configuration
- Database initialization

### 2. Test Adding Bills
```bash
python -m medical_bill_analyzer add tests/test_data/sample_bills/valid_bill.pdf
```

### 3. Test Other Commands
```bash
# List all bills
python -m medical_bill_analyzer list

# Calculate total costs
python -m medical_bill_analyzer total

# Get bonus recommendation
python -m medical_bill_analyzer bonus-check
```

## Full Testing Guide

For comprehensive step-by-step testing instructions with expected outputs, troubleshooting, and all command variations, see:

👉 **[TESTING_GUIDE.md](TESTING_GUIDE.md)**

## Developer Testing

If you want to test individual components programmatically, see:
- `scripts/test_llm_extraction.py` - Test LLM extraction directly
- `scripts/test_bill_extractor.py` - Test the complete extraction pipeline
- `pytest` - Run the automated test suite (395 tests, 95% coverage)
