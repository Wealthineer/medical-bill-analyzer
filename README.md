# Medical Bill Analyzer

A desktop application for German private health insurance (PKV) customers to analyze medical bills, track costs, and make informed decisions about claim submission versus annual bonus retention.

## Features

### Phase 1: Core Functionality (MVP)
- ✅ PDF bill processing with LLM-based information extraction
- ✅ Support for multiple LLM providers (Anthropic Claude, OpenAI GPT, local Ollama)
- ✅ Local SQLite database for data storage
- ✅ CLI commands for bill management
- ✅ Bonus vs. claim submission recommendation

### Phase 2: Enhanced Analytics
- ✅ Practitioner-level spending statistics
- ✅ Category breakdown with percentages
- ✅ Monthly time-series analysis
- ✅ CLI stats command with Rich tables

### Phase 4a: Interactive Text User Interface (TUI)
- ✅ Interactive dashboard with spending overview (current year)
- ✅ Navigate between screens with keyboard shortcuts (q, d, s, b, a)
- ✅ Add bills through wizard with detailed extraction preview
- ✅ Delete bills (X key in Bills screen, or after adding)
- ✅ View statistics with year navigation (practitioner breakdown)
- ✅ Smart path handling for drag-and-drop PDFs
- ✅ Auto-launches when no CLI args provided

### Phase 4b: Standalone Executable
- ✅ PyInstaller packaging for standalone executable
- ✅ No Python installation required
- ✅ First-run detection with automatic Settings redirect
- ✅ Build scripts for Linux, macOS, and Windows
- ✅ 44 MB executable size (well under 100 MB target)

### Future Phases
- **Phase 3**: Line item extraction and insurance coverage analysis

## Installation

There are two ways to install Medical Bill Analyzer:

### Option 1: Standalone Executable (Recommended for Users)

Download the pre-built executable for your platform - no Python installation required!

**Linux/macOS:**
```bash
# Download the release package
tar -xzvf medical-bill-analyzer-v1.0.0-linux.tar.gz
cd medical-bill-analyzer-v1.0.0-linux

# Run the application
./medical-bill-analyzer
```

**Windows:**
```bash
# Extract the zip file
# Run medical-bill-analyzer.exe
```

On first run, the application will automatically open the Settings screen to configure your LLM provider.

### Option 2: From Source (For Developers)

**Requirements:**
- Python 3.10 - 3.13
- Poetry (recommended) or pip

**Setup:**

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

3. Run the application:
```bash
# Launch TUI (interactive mode)
poetry run medical-bill-analyzer

# Or run specific commands
poetry run medical-bill-analyzer setup
poetry run medical-bill-analyzer add /path/to/bill.pdf
```

> **✅ Current Status**: Phases 1, 2, 4a, and 4b complete!
>
> - **TUI Mode** (recommended): Just run `medical-bill-analyzer` with no arguments for an interactive interface
> - **CLI Mode**: Use commands like `medical-bill-analyzer setup`, `medical-bill-analyzer add`, etc.
> - On first run, the app automatically guides you through setup

### First Run Setup

On first run (either packaged or from source), you'll be guided through:
- Choosing an LLM provider (Anthropic, OpenAI, LM Studio, or Ollama)
- Entering your API key (if using cloud provider)
- Setting your bonus threshold
- Testing the connection
- Initializing the database

All settings are stored in `~/.medical-bill-analyzer/data/`

## Usage

### Interactive TUI (Recommended)

The Text User Interface (TUI) provides an interactive terminal interface for easier navigation and better user experience.

**Launch TUI:**
```bash
# Auto-launches TUI if no arguments provided
medical-bill-analyzer
```

**TUI Features:**
- **Dashboard**: View current year summary (bills, costs, bonus status) and recent bills
- **Statistics**: Practitioner breakdown with year navigation (Previous/Next year buttons)
- **Bills**: List all bills with search and delete functionality (X key)
- **Add Wizard**: Multi-step wizard with detailed extraction preview and delete option
- **Settings**: Configure LLM providers, API keys, models, and app settings

**Keyboard Shortcuts:**
- `d` - Dashboard
- `s` - Statistics
- `b` - Bills
- `a` - Add Bills
- `c` - Settings
- `q` - Quit
- `x` - Delete selected bill (in Bills screen)
- `Esc` - Go back / Previous screen
- `r` - Refresh current view (Dashboard, Bills)

### CLI Commands

All functionality is also available via CLI commands:

#### Add bills
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

### Delete bills
```bash
# Delete a bill by ID (with confirmation)
medical-bill-analyzer delete 5

# Delete a bill without confirmation
medical-bill-analyzer delete 10 --force
```

**Note**: Use `medical-bill-analyzer list` to see all bills and their IDs.

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

### View spending statistics
```bash
# Show all practitioners by spending
medical-bill-analyzer stats --by practitioner

# Show top 10 practitioners
medical-bill-analyzer stats --by practitioner --top 10

# Show category breakdown for 2024
medical-bill-analyzer stats --by category --year 2024

# Show monthly trends
medical-bill-analyzer stats --by month --year 2024

# Filter by practitioner type
medical-bill-analyzer stats --by practitioner --type Zahnarzt
```

## Configuration

The application stores all configuration in the SQLite database at `~/.medical-bill-analyzer/data/medical_bills.db`.

**Configuration includes:**
- **LLM Provider**: Choose between Anthropic Claude, OpenAI GPT, LM Studio (local), or Ollama (local)
- **API Keys**: Stored securely in the database (for cloud providers)
- **Model Settings**: Model name, max tokens, temperature
- **Base URLs**: For LM Studio and Ollama local endpoints
- **Bonus Threshold**: Your annual PKV bonus amount in EUR
- **Storage Paths**: Database and PDF storage locations

**Configure via:**
1. **Setup Wizard** (first run): `medical-bill-analyzer setup`
2. **TUI Settings Screen**: Press `c` in the TUI to open Settings
3. **Direct Database**: All settings are in the `settings` table (single row)

**LM Studio Users**: Just paste the URL shown in LM Studio (e.g., `http://127.0.0.1:1234`). The app automatically adds `/v1` for OpenAI API compatibility.

## Data Privacy

- **Local Storage**: All PDFs, extracted data, settings, and API keys are stored locally in `~/.medical-bill-analyzer/data/`
- **Database Storage**: All configuration and credentials are in the SQLite database (not in config files or environment variables)
- **Cloud LLM Providers**: Only the extracted text is sent to the LLM API (not the PDF file itself)
- **Local Option**: Use LM Studio or Ollama for completely local processing with no data sent to external services

## Development

### Project Status

**Current Implementation**: All core phases complete!

**Phase 1 (Complete)**: Core Functionality (MVP)
- ✅ PDF bill processing with LLM-based extraction
- ✅ Support for Anthropic Claude, OpenAI GPT, and local Ollama
- ✅ SQLite database for local data storage
- ✅ CLI commands (setup, add, list, delete, total, bonus-check)

**Phase 2 (Complete)**: Enhanced Analytics
- ✅ Practitioner-level spending statistics
- ✅ Category breakdown with percentages
- ✅ Monthly time-series analysis
- ✅ Rich table output

**Phase 4a (Complete)**: Interactive Text User Interface
- ✅ Dashboard, Statistics, Bills, Add Wizard, Settings screens
- ✅ Keyboard navigation
- ✅ First-run detection

**Phase 4b (Complete)**: Packaging & Distribution
- ✅ PyInstaller standalone executable (44 MB)
- ✅ Build scripts for Linux, macOS, Windows
- ✅ No Python installation required

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for detailed progress tracking.

### Building the Executable

To build a standalone executable from source:

**Linux/macOS:**
```bash
# Build executable (runs tests first)
./scripts/build.sh

# Skip tests (faster, not recommended)
./scripts/build.sh --skip-tests

# Clean build artifacts first
./scripts/build.sh --clean
```

**Windows:**
```bash
scripts\build.bat
```

**Output:**
- Linux/macOS: `dist/medical-bill-analyzer` (44 MB)
- Windows: `dist/medical-bill-analyzer.exe`

**Create a release package:**
```bash
./scripts/package-release.sh [VERSION]
# Creates: releases/medical-bill-analyzer-v1.0.0-linux.tar.gz
```

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

**Run only unit tests (fast):**
```bash
pytest tests/unit/
```

**Run only integration tests:**
```bash
pytest tests/integration/
```

### Test Coverage

**Current Status**: 492 tests, 59% overall coverage

| Module | Tests | Coverage | Type |
|--------|-------|----------|------|
| Configuration | 15 | 91% | Unit |
| File utilities | 17 | 96% | Unit |
| Date utilities | 18 | 100% | Unit |
| Currency utilities | 21 | 95% | Unit |
| Validation | 18 | 93% | Unit |
| Exceptions | 10 | 100% | Unit |
| Database Models | 19 | 96% | Unit |
| Database Connection | 16 | 96% | Unit |
| Database Migrations | 20 | 87% | Unit |
| Bill Repository | 41 | 99% | Unit |
| PDF Extractor | 11 | 100% | Unit |
| PDF Validator | 19 | 100% | Unit |
| PDF Utils | 8 | 100% | Unit |
| **PDF Integration** | **19** | **100%** | **Integration** |
| **LLM Schemas** | **28** | **91%** | **Unit** |
| **LLM Prompts** | **14** | **100%** | **Unit** |
| **LLM Providers** | **14** | **86%** | **Unit** |
| **LLM Factory** | **12** | **78%** | **Unit** |
| **Extraction Result** | **10** | **100%** | **Unit** |
| **Bill Extractor** | **17** | **94%** | **Unit** |
| **Bill Processor** | **19** | **97%** | **Unit** |
| **Bonus Calculator** | **20** | **100%** | **Unit** |
| **Analytics Models** | **18** | **98%** | **Unit** |
| **Analytics Engine** | **23** | **100%** | **Unit** |
| **Analytics Integration** | **14** | **98%** | **Integration** |

**Testing Strategy:**
- **Unit tests (437)**: Fast, mocked dependencies, test all code paths
  - Includes 33 TUI tests using Textual's `run_test()`
- **Integration tests (33)**: Real PDFs and database, end-to-end validation
  - PDF integration: 19 tests with real German medical bill PDFs
  - Analytics integration: 14 tests with real database queries

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
├── test_data/               # Test data files
│   └── sample_bills/        # Sample German medical bill PDFs
│       ├── valid_bill.pdf
│       ├── multipage_bill.pdf
│       ├── minimal_text.pdf
│       └── empty_text.pdf
├── unit/                    # Unit tests (437 tests, mocked)
│   ├── test_config/         # Configuration module tests
│   ├── test_utils/          # Utility function tests
│   ├── test_core/           # Core module tests
│   ├── test_database/       # Database layer tests
│   ├── test_tui/            # TUI tests (33 tests)
│   ├── test_pdf/            # PDF processing tests (mocked)
│   └── test_llm/            # LLM provider tests (68 tests)
│       ├── test_schemas.py  # Pydantic schema validation (28 tests)
│       ├── test_prompts.py  # German medical bill prompts (14 tests)
│       ├── test_providers.py # Anthropic, OpenAI, Ollama providers (14 tests)
│       └── test_factory.py  # Provider factory pattern (12 tests)
└── integration/             # Integration tests (19 tests, real PDFs)
    └── test_pdf_processing.py  # End-to-end PDF tests with real files
```

**Regenerating Test PDFs:**
If needed, test PDFs can be regenerated:
```bash
python scripts/generate_test_pdfs.py
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
