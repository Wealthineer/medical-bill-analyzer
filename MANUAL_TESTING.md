# Manual Testing Guide - Phase 1.6

This guide shows how to manually test the implemented modules at the current stage (Phase 1.6).

## Current Status

✅ **Implemented:**
- Configuration management
- Database layer (SQLite)
- PDF text extraction
- LLM provider abstraction (Anthropic, OpenAI, Ollama)

❌ **Not Yet Implemented:**
- CLI commands (Phase 1.9)
- Extraction pipeline (Phase 1.7)
- Bill processor (Phase 1.8)

## Setup for Manual Testing

### 1. Set API Key

Set your Anthropic API key as an environment variable:

```bash
# macOS/Linux
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Windows (CMD)
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Or create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Use the Test Script

We'll create a simple test script to try out the components:

```bash
python scripts/test_llm_extraction.py
```

## Manual Testing Workflow

The test script will:
1. Load a sample German medical bill PDF
2. Extract text using pdfplumber
3. Send to Anthropic Claude for extraction
4. Parse and validate the response
5. Display the extracted information

## What to Look For

### Expected Output:
```
Loading PDF: tests/test_data/sample_bills/valid_bill.pdf
Extracted text: 245 characters

Sending to Anthropic Claude...
Response received successfully!

Extracted Information:
  Practitioner Name: Dr. med. Anna Müller
  Practitioner Type: Arzt
  Bill Date: 2024-03-15
  Bill Number: 2024-001234
  Total Amount: €29.49
  Currency: EUR

Validation: ✅ All fields valid
```

### Potential Issues:

1. **API Key Error**: `401 Unauthorized`
   - Check that ANTHROPIC_API_KEY is set correctly
   - Verify the key is valid

2. **Extraction Errors**: Missing or incorrect fields
   - The prompt may need adjustment
   - The PDF content may not match expected format

3. **JSON Parsing Errors**: Invalid response format
   - Claude may be wrapping JSON in markdown blocks (should auto-handle)
   - Check the raw response in error output

## Testing Other Providers

### OpenAI (GPT)
```bash
export OPENAI_API_KEY="sk-your-key-here"
# Edit scripts/test_llm_extraction.py to use "openai" provider
```

### Ollama (Local)
```bash
# Ensure Ollama is running: ollama serve
# Pull a model: ollama pull llama3.1:8b
# Edit scripts/test_llm_extraction.py to use "ollama" provider
```

## Next Steps After Testing

Once manual testing confirms the LLM extraction works:
1. **Phase 1.7**: Build extraction pipeline (orchestrates PDF + LLM)
2. **Phase 1.8**: Build bill processor (extraction + database storage)
3. **Phase 1.9**: Build CLI commands (user-friendly interface)

Then the usage shown in README.md will work!
