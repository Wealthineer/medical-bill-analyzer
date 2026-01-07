================================================================================
                      Medical Bill Analyzer
================================================================================

Version: 1.0.0
License: MIT
Platform: Cross-platform (Windows, macOS, Linux)

DESCRIPTION
-----------

Medical Bill Analyzer is a desktop application for German private health
insurance (PKV) customers to analyze medical bills, track costs, and make
informed decisions about claim submission versus annual bonus retention.

FEATURES
--------

- AI-Powered Extraction: Automatically extracts information from medical bill
  PDFs using LLM providers (Anthropic Claude, OpenAI GPT, or local Ollama)

- Spending Analytics: View statistics by practitioner, category, or month

- Bonus Decision Support: Get recommendations on whether to submit claims or
  keep your annual bonus based on your threshold

- Interactive TUI: Easy-to-use terminal interface for managing bills

- Privacy-Focused: All data is stored locally on your computer

SYSTEM REQUIREMENTS
-------------------

- Operating System: Windows 10+, macOS 10.14+, or Linux
- Terminal: Any modern terminal emulator
- Internet: Required for cloud LLM providers (not needed for local Ollama)
- Disk Space: ~100 MB for application + space for PDF storage

INSTALLATION
------------

1. Extract this archive to a location of your choice
2. Run the executable:
   - Linux/macOS: ./medical-bill-analyzer
   - Windows: medical-bill-analyzer.exe

No Python installation required!

LLM PROVIDER OPTIONS
--------------------

Anthropic Claude (Recommended)
  - Requires API key from https://console.anthropic.com/
  - Best extraction quality for German medical bills

OpenAI GPT
  - Requires API key from https://platform.openai.com/
  - Good extraction quality

LM Studio (Local)
  - Free, runs on your computer
  - Download from https://lmstudio.ai/
  - No API key required

Ollama (Local)
  - Free, runs on your computer
  - Install from https://ollama.ai/
  - No API key required

DATA PRIVACY
------------

- All PDFs are processed locally; only extracted text is sent to cloud LLMs
- All data is stored in your user directory
- API keys are stored locally in an encrypted database
- Use local LLM providers (Ollama/LM Studio) for complete offline operation

FILES IN THIS PACKAGE
---------------------

medical-bill-analyzer(.exe)  - Main application executable
GETTING_STARTED.txt          - Quick start guide
README.txt                   - This file
LICENSE.txt                  - MIT License

SUPPORT
-------

For documentation, issues, and source code:
https://github.com/Wealthineer/medical-bill-analyzer

================================================================================
