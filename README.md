# Medical Bill Analyzer

A desktop application for German private health insurance (PKV) customers to analyze medical bills, track costs, and make informed decisions about claim submission versus annual bonus retention.

## Features

### Phase 1: Core Functionality (MVP)
- ✅ PDF bill processing with LLM-based information extraction
- ✅ Support for multiple LLM providers (Anthropic Claude, OpenAI GPT, local Ollama)
- ✅ Local SQLite database for data storage
- ✅ CLI commands for bill management
- ✅ Bonus vs. claim submission recommendation

### Future Phases
- **Phase 2**: Enhanced analytics (practitioner and category statistics, time-series analysis)
- **Phase 3**: Line item extraction and insurance coverage analysis
- **Phase 4a**: Interactive Text User Interface (TUI)
- **Phase 4b**: Standalone executable packaging

## Installation

### Requirements
- Python 3.10 or higher
- pip or poetry

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd medical-bill-analyzer
```

2. Install dependencies using Poetry:
```bash
poetry install
```

Or using pip:
```bash
pip install -e .
```

3. Run the setup wizard:
```bash
medical-bill-analyzer setup
```

The setup wizard will guide you through:
- Choosing an LLM provider (Anthropic, OpenAI, or Ollama)
- Entering your API key (if using cloud provider)
- Setting your bonus threshold
- Testing the connection
- Initializing the database

## Usage

### Add bills
```bash
# Add a single bill
medical-bill-analyzer add /path/to/bill.pdf

# Add multiple bills from a directory
medical-bill-analyzer add /path/to/bills/ --recursive

# Add with notes
medical-bill-analyzer add /path/to/bill.pdf --note "Emergency visit"
```

### List bills
```bash
# List all bills
medical-bill-analyzer list

# List bills for specific year
medical-bill-analyzer list --year 2024

# List bills requiring review
medical-bill-analyzer list --status needs_review
```

### Calculate totals
```bash
# Show total for current year
medical-bill-analyzer total

# Show total for specific year
medical-bill-analyzer total --year 2024

# Show total for date range
medical-bill-analyzer total --from 2024-01-01 --to 2024-12-31
```

### Check bonus recommendation
```bash
# Check against default bonus threshold
medical-bill-analyzer bonus-check

# Check against specific threshold
medical-bill-analyzer bonus-check --threshold 1000
```

## Configuration

The application stores configuration in `~/.medical-bill-analyzer/config.yaml` (or `%APPDATA%/medical-bill-analyzer/config.yaml` on Windows).

Example configuration:
```yaml
llm:
  provider: anthropic  # Options: anthropic, openai, ollama
  anthropic:
    model: claude-sonnet-4-20250514
    api_key_env: ANTHROPIC_API_KEY
    max_tokens: 1000
    temperature: 0

storage:
  database_path: ~/.medical-bill-analyzer/data/medical_bills.db
  pdf_storage_path: ~/.medical-bill-analyzer/data/pdfs/

bonus:
  default_threshold: 1000  # EUR
```

## Data Privacy

- **Local Storage**: All PDFs and extracted data are stored locally on your machine
- **Cloud LLM Providers**: Only the extracted text is sent to the LLM API (not the PDF file itself)
- **Local Option**: Use Ollama for completely local processing with no data sent to external services

## Development

### Project Status

**Current Implementation**: Phase 1.1-1.5 Complete (50%)
- ✅ Project infrastructure setup
- ✅ Configuration management
- ✅ Utilities and logging
- ✅ Database layer with SQLite
- ✅ PDF processing pipeline
- ✅ Comprehensive automated tests (232 tests, 92% coverage)

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for detailed progress tracking.

### Running Tests

The project includes a comprehensive automated test suite covering all implemented modules.

**Run all tests:**
```bash
pytest
```

**Run with coverage report:**
```bash
pytest --cov=medical_bill_analyzer --cov-report=html --cov-report=term
```

**Run specific test module:**
```bash
pytest tests/unit/test_config/
pytest tests/unit/test_utils/test_date_utils.py
```

### Test Coverage

**Current Status**: 232 tests, 92% overall coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Configuration | 15 | 91% |
| File utilities | 17 | 96% |
| Date utilities | 18 | 100% |
| Currency utilities | 21 | 95% |
| Validation | 18 | 93% |
| Exceptions | 10 | 100% |
| Database Models | 19 | 96% |
| Database Connection | 16 | 96% |
| Database Migrations | 20 | 87% |
| Bill Repository | 41 | 99% |
| PDF Extractor | 11 | 100% |
| PDF Validator | 19 | 100% |
| PDF Utils | 8 | 100% |

**View detailed coverage report:**
After running tests with coverage, open `htmlcov/index.html` in your browser:
```bash
pytest --cov=medical_bill_analyzer --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── unit/                    # Unit tests
│   ├── test_config/         # Configuration module tests
│   ├── test_utils/          # Utility function tests
│   ├── test_core/           # Core module tests
│   ├── test_database/       # Database layer tests
│   └── test_pdf/            # PDF processing tests
└── integration/             # Integration tests (future)
```

### Code Formatting
```bash
poetry run black src tests
poetry run ruff check src tests
```

### Type Checking
```bash
poetry run mypy src
```

### Development Workflow

1. **Create a new feature branch**
2. **Implement the feature** (refer to task files in `docs/tasks/`)
3. **Write tests** for the new functionality
4. **Run tests** and ensure all pass with good coverage
5. **Format code** with black and ruff
6. **Update documentation** (IMPLEMENTATION.md, phase task files)
7. **Commit changes** with descriptive messages

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.
