# Medical Bill Analyzer - Technical Specification

## Project Overview

A desktop application for German private health insurance (PKV) customers to analyze medical bills, track costs, and make informed decisions about claim submission versus annual bonus retention.

## Target User

Private health insurance customers in Germany who:
- Receive individual bills from multiple medical practitioners
- Need to decide whether to submit claims or retain annual bonus
- Want to track and analyze their medical expenses over time

## Technology Stack Recommendations

- **Language**: Python 3.10+
- **PDF Processing**: `pdfplumber` or `pypdf`
- **LLM Integration**: 
  - Cloud: Anthropic Claude API (via `anthropic` SDK) or OpenAI API (via `openai` SDK)
  - Local: Ollama (via `ollama` Python client or direct HTTP requests)
- **Data Storage**: SQLite for local database
- **CLI Framework**: `click` or `typer` for command-line interface
- **TUI Framework**: `textual` or `rich` for interactive terminal UI (Phase 4)
- **Packaging**: `PyInstaller` or `py2app`/`py2exe` for standalone executables (Phase 4)

## Core Principles

1. **Privacy First**: All data stored locally, PDFs never leave the user's machine except text extraction sent to LLM (if using cloud models)
2. **Model Flexibility**: Support multiple LLM providers (cloud and local) through abstraction layer
3. **Incremental Processing**: Bills can be added one at a time or in batches
4. **Extensibility**: Design database schema to accommodate future features
5. **German Context**: Handle German medical bill formats, terminology (GOÄ, EBM codes), and currency
6. **User-Friendly**: Start with CLI, evolve to TUI, package as standalone executable

---

## Phase 1: Core Functionality - Bill Processing & Basic Totals

### Goal
Extract information from PDFs and calculate total costs to enable bonus vs. claim submission decisions.

### Features

#### 1.0 First-Run Setup Wizard
- **Command**: `python app.py setup`
- **Interactive prompts**:
  1. Welcome message and privacy notice
  2. Choose LLM provider:
     - Option 1: Anthropic Claude (API key required)
     - Option 2: OpenAI GPT-4 (API key required)
     - Option 3: Local Ollama (checks if installed, offers installation guidance)
  3. Enter API key (if cloud provider selected)
  4. Test connection with sample extraction
  5. Set default bonus threshold (optional)
  6. Initialize database and directory structure
- **Output**: Creates `config.yaml` with user preferences
- **Validation**: Test API connection or Ollama availability before proceeding

#### 1.1 LLM Provider Abstraction Layer
- **Interface**: Create abstract `LLMProvider` class with `extract()` method
- **Implementations**:
  - `AnthropicProvider`: Uses Anthropic API
  - `OpenAIProvider`: Uses OpenAI API
  - `OllamaProvider`: Uses local Ollama with configurable model (default: `llama3.1:8b`)
- **Configuration**: Load provider from `config.yaml`
- **Graceful degradation**: If configured provider unavailable, prompt user to reconfigure
- **Provider-specific settings**:
  - Cloud: API key, model name, temperature, max_tokens
  - Local: Ollama host URL (default: `http://localhost:11434`), model name

#### 1.2 PDF Text Extraction
- **Input**: Directory path or individual PDF file(s)
- **Process**: Extract text content from PDF using `pdfplumber`
- **Error Handling**: 
  - Skip corrupted PDFs with warning
  - Handle scanned PDFs (detect lack of text, suggest OCR in future)
- **Output**: Raw text string per PDF

#### 1.3 LLM-Based Information Extraction
- **Input**: Raw text from PDF
- **LLM Prompt Template**:
  ```
  You are analyzing a German medical bill (Arztrechnung). Extract the following information and return it as JSON:
  
  {
    "practitioner_name": "Full name of doctor or clinic",
    "practitioner_type": "One of: Arzt, Zahnarzt, Heilpraktiker, Krankenhaus, Labor, Apotheke, Sonstige",
    "bill_date": "Date in YYYY-MM-DD format",
    "bill_number": "Invoice/bill number if present",
    "total_amount": "Total amount in EUR as decimal number",
    "currency": "EUR"
  }
  
  If any field cannot be determined, use null.
  
  Bill text:
  [TEXT]
  ```
- **API Configuration**:
  - Model: `claude-sonnet-4-20250514` (balance of cost and quality)
  - Max tokens: 1000
  - Temperature: 0 (deterministic output)
- **Response Parsing**: Parse JSON, validate structure
- **Error Handling**: Retry once on API failure, log extraction failures

#### 1.4 Data Storage - Database Schema

**Table: `bills`**
```sql
CREATE TABLE bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,  -- SHA256 of PDF to detect duplicates
    pdf_path TEXT NOT NULL,
    practitioner_name TEXT,
    practitioner_type TEXT,
    bill_date DATE,
    bill_number TEXT,
    total_amount DECIMAL(10,2),
    currency TEXT DEFAULT 'EUR',
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_status TEXT DEFAULT 'success',  -- success, failed, needs_review
    raw_extraction_json TEXT,  -- Store full LLM response for debugging
    notes TEXT
);

CREATE INDEX idx_bill_date ON bills(bill_date);
CREATE INDEX idx_practitioner_name ON bills(practitioner_name);
CREATE INDEX idx_practitioner_type ON bills(practitioner_type);
```

#### 1.5 CLI Commands - Phase 1

**Command: `setup`** (First-run only)
```bash
# Interactive setup wizard
python app.py setup

# Non-interactive setup with flags
python app.py setup --provider anthropic --api-key sk-xxx --threshold 1000
```

**Command: `add`**
```bash
# Add single bill
python app.py add /path/to/bill.pdf

# Add multiple bills from directory
python app.py add /path/to/bills/ --recursive

# Add with notes
python app.py add /path/to/bill.pdf --note "Emergency visit"
```

**Command: `list`**
```bash
# List all bills
python app.py list

# List bills for specific year
python app.py list --year 2024

# List bills requiring review
python app.py list --status needs_review
```

**Command: `total`**
```bash
# Show total for current year
python app.py total

# Show total for specific year
python app.py total --year 2024

# Show total for date range
python app.py total --from 2024-01-01 --to 2024-12-31
```

**Command: `bonus-check`**
```bash
# Check against bonus threshold
python app.py bonus-check --threshold 1000

# Output:
# Total medical costs (2024): €847.50
# Your bonus threshold: €1,000.00
# Recommendation: Don't submit claims - you'll save €152.50 by keeping the bonus
```

#### 1.6 Output Format - Phase 1
- Simple table format in terminal using `tabulate`
- Summary statistics (count, total, average per bill)
- Color coding: green for under threshold, red for over

### Acceptance Criteria - Phase 1
- [ ] Setup wizard guides user through initial configuration
- [ ] Supports at least 2 LLM providers (1 cloud, 1 local)
- [ ] Provider abstraction allows easy addition of new providers
- [ ] Can process a single PDF and extract basic information
- [ ] Can process multiple PDFs in batch
- [ ] Duplicate PDFs are detected and skipped
- [ ] Total costs can be calculated for any date range
- [ ] Bonus comparison provides clear recommendation
- [ ] All data stored locally in SQLite database

---

## Phase 2: Enhanced Analytics - Practitioner & Category Analysis

### Goal
Provide detailed breakdowns by practitioner and category to understand spending patterns.

### Features

#### 2.1 Practitioner Statistics
- **Grouping**: Aggregate all bills by practitioner name
- **Metrics per practitioner**:
  - Total amount spent
  - Number of visits/bills
  - Average cost per visit
  - Date range (first to last visit)
  - Most recent visit date

#### 2.2 Category Statistics
- **Grouping**: Aggregate by practitioner_type
- **Metrics per category**:
  - Total amount
  - Number of bills
  - Percentage of total spending
  - Average per bill in category

#### 2.3 Time-Series Analysis
- **Monthly breakdown**: Costs per month
- **Quarterly breakdown**: Costs per quarter
- **Year-over-year comparison**: Compare current year vs. previous years

#### 2.4 CLI Commands - Phase 2

**Command: `stats`**
```bash
# Show all statistics for current year
python app.py stats

# Statistics by practitioner
python app.py stats --by practitioner

# Statistics by category
python app.py stats --by category

# Monthly breakdown
python app.py stats --by month --year 2024

# Top N practitioners by spending
python app.py stats --top 5
```

**Command: `practitioner`**
```bash
# Show details for specific practitioner
python app.py practitioner "Dr. Schmidt"

# List all practitioners
python app.py practitioner --list
```

#### 2.5 Output Enhancements - Phase 2
- Bar charts in terminal using `plotille` or similar
- Percentage breakdowns with visual indicators
- Comparison tables (e.g., Q1 2024 vs Q1 2023)

### Acceptance Criteria - Phase 2
- [ ] Can generate practitioner-level spending report
- [ ] Can generate category-level spending report
- [ ] Can show monthly/quarterly spending trends
- [ ] Can identify top spending practitioners
- [ ] Outputs are clear and actionable

---

## Phase 3: Line Item Analysis & Contract Comparison

### Goal
Extract individual line items from bills to compare against insurance contract coverage and identify optimization opportunities.

### Features

#### 3.1 Enhanced LLM Extraction - Line Items
- **Updated LLM Prompt**:
  ```
  Extract all line items from this German medical bill. For each service/item, extract:
  
  {
    "practitioner_info": { ... },  // Same as Phase 1
    "line_items": [
      {
        "position": "Line item number if present",
        "date": "Service date in YYYY-MM-DD",
        "goa_code": "GOÄ or EBM code if present",
        "description": "Service description in German",
        "quantity": "Number as decimal",
        "unit_price": "Price per unit in EUR",
        "total_price": "Total for this line in EUR",
        "factor": "GOÄ factor if applicable (e.g., 2.3)"
      }
    ]
  }
  ```

#### 3.2 Database Schema Extension

**Table: `line_items`**
```sql
CREATE TABLE line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER NOT NULL,
    position TEXT,
    service_date DATE,
    goa_code TEXT,
    description TEXT,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    factor DECIMAL(3,2),
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE
);

CREATE INDEX idx_goa_code ON line_items(goa_code);
CREATE INDEX idx_service_date ON line_items(service_date);
```

**Table: `contract_coverage`** (User-defined)
```sql
CREATE TABLE contract_coverage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goa_code TEXT UNIQUE,
    description TEXT,
    max_factor DECIMAL(3,2),  -- Max GOÄ factor covered
    coverage_percentage INTEGER,  -- % covered (e.g., 80, 100)
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.3 Contract Coverage Analysis
- **Input**: User manually adds coverage rules (or imports from contract PDF)
- **Process**:
  - Match line items against contract_coverage by GOÄ code
  - Calculate covered amount vs. total amount per line item
  - Flag items: fully_covered, partially_covered, not_covered, unknown
- **Output**: Report showing what would be reimbursed

#### 3.4 Line Item Statistics
- **Most common procedures**: Ranked by frequency
- **Most expensive procedures**: Ranked by total cost
- **Average cost per GOÄ code**: Identify price variations
- **Factor analysis**: Show average factor charged per GOÄ code vs. contract max

#### 3.5 CLI Commands - Phase 3

**Command: `line-items`**
```bash
# Show all line items for a bill
python app.py line-items --bill-id 5

# Show all line items for a date range
python app.py line-items --from 2024-01-01 --to 2024-12-31

# Filter by GOÄ code
python app.py line-items --goa 1

# Show most common procedures
python app.py line-items --top 10
```

**Command: `coverage`**
```bash
# Add coverage rule
python app.py coverage add --goa 1 --max-factor 2.3 --percentage 100

# Import coverage from CSV
python app.py coverage import contract.csv

# Check coverage for specific bill
python app.py coverage check --bill-id 5

# Coverage report for year
python app.py coverage report --year 2024
```

**Command: `reprocess`**
```bash
# Reprocess specific bill with line item extraction
python app.py reprocess --bill-id 5

# Reprocess all bills (useful after LLM prompt improvements)
python app.py reprocess --all --extract-line-items
```

#### 3.6 Coverage Analysis Output
```
Coverage Report for 2024
========================

Total Billed: €2,450.00
Estimated Covered: €2,100.00 (85.7%)
Not Covered: €350.00 (14.3%)

Breakdown by Coverage Status:
- Fully Covered: €1,800.00 (73.5%)
- Partially Covered: €300.00 (12.2%)
- Not Covered: €200.00 (8.2%)
- Unknown (No Coverage Data): €150.00 (6.1%)

Top 5 Most Expensive Non-Covered Items:
1. GOÄ 3500 - Alternative Medicine - €80.00
2. GOÄ 5855 - Ultrasound (Factor 3.5) - €65.00 (Factor exceeds contract max 2.3)
...
```

### Acceptance Criteria - Phase 3
- [ ] Can extract line items from bills
- [ ] Can store and manage contract coverage rules
- [ ] Can calculate coverage for individual line items
- [ ] Can generate coverage analysis report
- [ ] Can identify most expensive non-covered items
- [ ] Can show factor violations (charged factor > contract max)

---

## Phase 4: User Experience & Distribution

### Goal
Transform the CLI app into a user-friendly tool accessible to non-technical users through an interactive terminal interface and standalone executable distribution.

---

### Phase 4a: Text User Interface (TUI)

#### 4a.1 TUI Framework Selection
- **Recommended**: `textual` - Modern, reactive TUI framework with rich widgets
- **Alternative**: `rich` + custom layout - Lighter weight but less interactive

#### 4a.2 TUI Features

**Main Dashboard Screen**
```
┌─ Medical Bill Analyzer ────────────────────────────────────────────┐
│                                                                     │
│  📊 2024 Summary                                                    │
│  ─────────────────────────────────────────────────────────────────│
│  Total Bills: 23                    Total Cost: €2,450.00          │
│  Bonus Threshold: €1,000.00         Status: ⚠️  OVER THRESHOLD     │
│                                                                     │
│  📁 Recent Bills                                                    │
│  ─────────────────────────────────────────────────────────────────│
│  ┃ Date       │ Practitioner          │ Amount   │ Status          │
│  ┣━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━┿━━━━━━━━━━┿━━━━━━━━━━━━━━━━┫
│  ┃ 2024-12-01 │ Dr. Schmidt          │ €120.00  │ ✓ Processed    │
│  ┃ 2024-11-28 │ Zahnarztpraxis Müller│ €380.50  │ ✓ Processed    │
│  ┃ 2024-11-20 │ Labor Berlin         │ €85.00   │ ⚠ Needs Review │
│                                                                     │
│  [A]dd Bills  [S]tatistics  [C]overage  [E]xport  [Q]uit          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Statistics Screen**
- Interactive charts using ASCII/Unicode box drawing
- Tabs: By Practitioner | By Category | Monthly Trend
- Drill-down: Click practitioner to see all their bills
- Visual indicators: Bar charts, pie charts (text-based)

**Bill Management Screen**
- Table view of all bills with sort/filter
- Select bill to view details/edit
- Batch operations: mark for review, add notes, delete
- Search functionality

**Add Bills Wizard**
- Step 1: Select files (file picker or drag-drop paths)
- Step 2: Processing progress bar with real-time status
- Step 3: Review extracted data, flag issues
- Step 4: Confirm and save

**Coverage Analysis Screen** (Phase 3 integration)
- Visual breakdown of covered vs. not covered
- Highlight expensive non-covered items
- Interactive: click item to see contract rule

#### 4a.3 TUI Commands Integration
- All existing CLI commands remain functional
- TUI launches with: `python app.py` (no arguments) or `python app.py tui`
- TUI wraps CLI logic, doesn't replace it
- Use `--no-tui` flag to force CLI mode

#### 4a.4 Keyboard Shortcuts
- `a`: Add bills
- `s`: Statistics view
- `c`: Coverage analysis
- `e`: Export data
- `r`: Refresh data
- `?`: Help/keyboard shortcuts
- `/`: Search
- `q`: Quit
- Arrow keys: Navigate
- Enter: Select/drill down
- Escape: Go back

#### 4a.5 TUI Accessibility
- High contrast mode support
- Color-blind friendly palette option
- Screen reader compatibility (where possible)
- Configurable font size (terminal dependent)

### Acceptance Criteria - Phase 4a
- [ ] TUI launches successfully and displays dashboard
- [ ] Can add bills through TUI wizard
- [ ] Can navigate all major screens with keyboard
- [ ] TUI gracefully degrades if terminal doesn't support rich features
- [ ] All CLI functionality accessible through TUI
- [ ] TUI state persists (remembers last view, filters)

---

### Phase 4b: Standalone Executable Packaging

#### 4b.1 Packaging Strategy

**Tool Selection: PyInstaller**
- Cross-platform support (Windows, macOS, Linux)
- Single-file executable option
- Can bundle data files (config templates, etc.)

**Alternative: Briefcase**
- Creates native installers for each platform
- Better macOS integration (proper .app bundle)
- More professional distribution

#### 4b.2 Build Configuration

**PyInstaller spec file** (`medical-bill-analyzer.spec`):
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml.template', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'anthropic',
        'openai', 
        'ollama',
        'pdfplumber',
        'textual',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='medical-bill-analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'  # Optional: Add app icon
)
```

#### 4b.3 Build Process

**Automated builds for each platform:**

```bash
# Build script: build.sh (Linux/macOS) or build.bat (Windows)

# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller medical-bill-analyzer.spec

# Output: dist/medical-bill-analyzer (or .exe on Windows)

# Test executable
./dist/medical-bill-analyzer setup
```

**GitHub Actions CI/CD** (optional but recommended):
- Automatically build for Windows, macOS, Linux on each release
- Upload binaries as release artifacts
- Run automated tests before building

#### 4b.4 Distribution Structure

**Release package contents:**
```
medical-bill-analyzer-v1.0.0-windows/
├── medical-bill-analyzer.exe
├── README.txt
├── LICENSE.txt
├── GETTING_STARTED.txt
└── config.yaml.template

medical-bill-analyzer-v1.0.0-macos/
├── medical-bill-analyzer
├── README.txt
├── LICENSE.txt
├── GETTING_STARTED.txt
└── config.yaml.template

medical-bill-analyzer-v1.0.0-linux/
├── medical-bill-analyzer
├── README.txt
├── LICENSE.txt
├── GETTING_STARTED.txt
└── config.yaml.template
```

#### 4b.5 First-Run Experience (Packaged App)

**When user runs executable for first time:**
1. Detect no config file exists
2. Auto-launch setup wizard (from Phase 1)
3. Create `~/.medical-bill-analyzer/` directory for data
4. Create `config.yaml` in that directory
5. Initialize database in user's home directory
6. Prompt for LLM provider setup
7. Test connection
8. Launch TUI (if supported) or show CLI usage

**Subsequent runs:**
- Check for config, load settings
- Launch TUI by default (or CLI with `--no-tui`)

#### 4b.6 Installation Instructions

**Windows:**
```
1. Download medical-bill-analyzer-v1.0.0-windows.zip
2. Extract to a folder (e.g., C:\Program Files\MedicalBillAnalyzer)
3. Double-click medical-bill-analyzer.exe
4. Follow the setup wizard
5. (Optional) Create desktop shortcut
```

**macOS:**
```
1. Download medical-bill-analyzer-v1.0.0-macos.zip
2. Extract and move to Applications folder
3. Right-click > Open (first time only, to bypass Gatekeeper)
4. Follow the setup wizard
5. (Optional) Add to Dock
```

**Linux:**
```
1. Download medical-bill-analyzer-v1.0.0-linux.tar.gz
2. Extract: tar -xzf medical-bill-analyzer-v1.0.0-linux.tar.gz
3. Make executable: chmod +x medical-bill-analyzer
4. Run: ./medical-bill-analyzer
5. (Optional) Move to /usr/local/bin for system-wide access
```

#### 4b.7 Updates & Versioning

**Update mechanism options:**

**Option 1: Manual updates**
- User downloads new version
- Replaces old executable
- Config and data remain in user's home directory (untouched)

**Option 2: Built-in update checker**
- App checks GitHub releases on startup (optional setting)
- Notifies user of new version
- Provides download link
- Does not auto-download (privacy/security)

**Version display:**
```bash
medical-bill-analyzer --version
# Output: Medical Bill Analyzer v1.0.0

medical-bill-analyzer about
# Shows version, provider info, license, support link
```

#### 4b.8 Size Optimization

**Executable size concerns:**
- Base Python + dependencies: ~50-80MB
- With local LLM support (Ollama client only): +5MB
- Single-file executable: Convenient but larger
- Consider "onedir" mode: Folder with multiple files, smaller but less portable

**Size reduction strategies:**
1. Exclude unnecessary dependencies (e.g., don't bundle unused LLM providers)
2. Use UPX compression (PyInstaller option)
3. Strip debug symbols
4. Provide "lite" version without TUI for smaller size

### Acceptance Criteria - Phase 4b
- [ ] Can build standalone executable for at least 2 platforms
- [ ] Executable runs on clean machine without Python installed
- [ ] Setup wizard works correctly on first run
- [ ] Config and data stored in appropriate user directory
- [ ] App remains under 100MB (uncompressed)
- [ ] Clear installation instructions for each platform
- [ ] Version information accessible via CLI

---

### Phase 4c: Advanced Features (Future Enhancements)

#### 4c.1 Export & Reporting
- **PDF Report Generation**: Summary report suitable for submission to insurance
- **CSV Export**: All data for external analysis
- **Excel Export**: Formatted workbook with multiple sheets (summary, by practitioner, by category)

#### 4c.2 Multi-Year Analysis
- **Year-over-year comparison**: Spending trends across multiple years
- **Budget forecasting**: Based on historical data, predict annual costs
- **Bonus optimization**: Multi-year strategy (submit every 2-3 years vs. annually)

#### 4c.3 OCR Support
- **Scanned PDFs**: Use Tesseract OCR for image-based PDFs
- **Image uploads**: Support JPG/PNG of paper bills
- **Note**: OCR significantly increases package size (~100MB for Tesseract)

#### 4c.4 Smart Notifications
- **Threshold alerts**: Email/notification when approaching bonus threshold
- **Missing data alerts**: Bills that couldn't be processed properly
- **End of year summary**: Automated annual report

#### 4c.5 Advanced Contract Management
- **Multiple contracts**: Support for family members with different contracts
- **Contract versioning**: Track changes over time
- **Automated contract parsing**: Extract coverage rules from insurance contract PDFs

#### 4c.6 Web UI Alternative
- **Streamlit Dashboard** (alternative to TUI):
  - Upload PDFs via drag-and-drop
  - Interactive charts and graphs (using Plotly)
  - Edit/review extracted data in table
  - Visual coverage analysis
- **Note**: Web UI would be separate from TUI, not a replacement
- **Distribution**: Could offer web version as Docker container

---

## Implementation Notes

### Error Handling Strategy
1. **PDF Processing Errors**: Log, skip file, continue processing others
2. **LLM API Errors**: Retry once, then mark bill as "needs_review"
3. **Data Validation**: Check for reasonable values (e.g., amount > 0, date in past)
4. **Duplicate Detection**: Use file hash to prevent re-processing

### Data Privacy
- All PDFs and extracted data stored locally
- Only text content sent to LLM API (not the PDF itself)
- Option to redact sensitive information before LLM processing
- Database encryption optional (SQLCipher)

### Configuration File
Create `config.yaml`:
```yaml
llm:
  provider: anthropic  # Options: anthropic, openai, ollama
  
  # Cloud provider settings (used if provider is anthropic or openai)
  anthropic:
    model: claude-sonnet-4-20250514
    api_key_env: ANTHROPIC_API_KEY  # Reference to environment variable
    max_tokens: 1000
    temperature: 0
  
  openai:
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY
    max_tokens: 1000
    temperature: 0
  
  # Local provider settings (used if provider is ollama)
  ollama:
    host: http://localhost:11434
    model: llama3.1:8b  # or mistral, phi3, etc.
    timeout: 60

storage:
  database_path: ./data/medical_bills.db
  pdf_storage_path: ./data/pdfs/

bonus:
  default_threshold: 1000  # EUR
  
extraction:
  retry_attempts: 1
  extract_line_items: false  # Phase 3 feature, disabled initially
```

### Testing Strategy
1. **Unit Tests**: Individual extraction functions, database operations
2. **Integration Tests**: End-to-end bill processing
3. **Test Data**: Include sample anonymized German medical bills
4. **LLM Mock**: For CI/CD, mock LLM responses to avoid API costs

### Deployment & Distribution
- **Development**: Standard Python package with `requirements.txt` or `pyproject.toml`
- **Distribution**: Standalone executables via PyInstaller (Phase 4b)
- **Platforms**: Windows (.exe), macOS (binary), Linux (binary)
- **Installation**: 
  - Development: `pip install -e .` for local development
  - End-users: Download executable, no installation needed
- **First-run setup**: Interactive wizard initializes config and database
- **Updates**: Manual download of new versions (automated update checker optional in Phase 4c)

---

## Development Roadmap

### Sprint 1 (Week 1-2): Phase 1 MVP
- [ ] Set up project structure, dependencies
- [ ] Implement setup wizard with provider selection
- [ ] Create LLM provider abstraction layer (Anthropic, OpenAI, Ollama)
- [ ] Implement PDF text extraction
- [ ] Implement basic LLM extraction (without line items)
- [ ] Create database schema (bills table only)
- [ ] Implement `setup`, `add`, `list`, `total`, `bonus-check` commands
- [ ] Basic error handling and logging
- [ ] Write README with setup instructions
- [ ] Test with all 3 provider types

### Sprint 2 (Week 3): Phase 2 Analytics
- [ ] Implement practitioner statistics
- [ ] Implement category statistics
- [ ] Implement time-series analysis (monthly/quarterly)
- [ ] Add `stats` and `practitioner` commands
- [ ] Improve output formatting with charts

### Sprint 3 (Week 4-5): Phase 3 Line Items
- [ ] Enhance LLM prompt for line item extraction
- [ ] Extend database schema (line_items, contract_coverage)
- [ ] Implement coverage analysis logic
- [ ] Add `line-items`, `coverage`, `reprocess` commands
- [ ] Create coverage report generator

### Sprint 4 (Week 6-7): Phase 4a TUI
- [ ] Set up Textual framework
- [ ] Create main dashboard screen
- [ ] Implement navigation system
- [ ] Build statistics screen with interactive charts
- [ ] Create bill management screen
- [ ] Implement add bills wizard
- [ ] Build coverage analysis screen (if Phase 3 complete)
- [ ] Add keyboard shortcuts
- [ ] Test TUI on different terminal types
- [ ] Ensure CLI commands still work

### Sprint 5 (Week 8-9): Phase 4b Packaging
- [ ] Set up PyInstaller configuration
- [ ] Create build scripts for Windows, macOS, Linux
- [ ] Test executables on clean machines (VM or test devices)
- [ ] Optimize executable size
- [ ] Write installation instructions
- [ ] Create GETTING_STARTED guide
- [ ] Set up GitHub Actions for automated builds (optional)
- [ ] Create release packages
- [ ] Test first-run experience on all platforms

### Sprint 6 (Week 10+): Phase 4c Polish & Extensions
- [ ] Implement export features
- [ ] Add OCR support for scanned PDFs (optional)
- [ ] Build update checker
- [ ] Comprehensive documentation
- [ ] Video tutorial for setup and usage
- [ ] User feedback collection and iteration

---

## Success Metrics

### Phase 1 Success
- User can process 10+ bills in under 2 minutes
- Extraction accuracy > 95% for practitioner name and total amount
- Clear bonus recommendation provided
- Setup wizard completes successfully for all provider types
- Works with both cloud and local LLMs

### Phase 2 Success
- User gains actionable insights into spending patterns
- Can identify which practitioners are most expensive
- Can see spending trends over time

### Phase 3 Success
- User can identify which services are not covered by insurance
- Can estimate reimbursement amount before submission
- Can optimize claims by removing non-covered items

### Phase 4a Success (TUI)
- Non-technical users can navigate app without CLI knowledge
- TUI provides visual feedback and intuitive workflows
- App feels modern and professional
- All functionality accessible via TUI

### Phase 4b Success (Packaging)
- Executable runs on clean machine without any prerequisites
- Installation takes < 5 minutes including setup wizard
- Package size < 100MB (or < 150MB with OCR)
- Users report successful installation on Windows/macOS/Linux

---

## Appendix: German Medical Bill Context

### Common Practitioner Types
- **Arzt**: General or specialist physician
- **Zahnarzt**: Dentist
- **Heilpraktiker**: Alternative medicine practitioner
- **Krankenhaus**: Hospital
- **Labor**: Laboratory
- **Apotheke**: Pharmacy
- **Physiotherapie**: Physical therapy

### GOÄ (Gebührenordnung für Ärzte)
- Standard fee schedule for German physicians
- Each procedure has a code and base price
- Doctors can charge a factor (typically 1.0 to 3.5) times the base price
- Insurance contracts usually specify max factor covered (e.g., 2.3x)

### EBM (Einheitlicher Bewertungsmaßstab)
- Fee schedule for statutory health insurance (less relevant for PKV but may appear)

### Typical Bill Structure
1. Header: Practitioner info, patient info, bill number, date
2. Line items: Each service with code, description, factor, price
3. Subtotals: Sometimes grouped by category
4. Total: Final amount due

### Private Insurance Bonus Systems
- Typical thresholds: €600 - €1,500 per year
- If no claims submitted, get X% of contributions back (or fixed amount)
- Strategic decision: submit small claims vs. wait for major expenses

---

## Questions for Clarification

Before starting implementation, confirm:
1. **LLM Provider Preference**: Which providers should be prioritized in Phase 1?
   - Anthropic Claude (requires API key)
   - OpenAI GPT-4 (requires API key)
   - Local Ollama (requires Ollama installation)
   - All three?
2. **Multi-user support**: Single-user or multiple family members with separate profiles?
3. **Multiple insurance contracts**: Should the app handle different contracts (e.g., family members)?
4. **Your typical bonus threshold**: What's your specific threshold to test against?
5. **Test data availability**: Do you have existing bills to test with during development?
6. **TUI Priority**: Is TUI essential for MVP or can it wait until Phase 4a?
7. **Platform Priority**: Which platform should be tested first for packaging?
   - Windows
   - macOS
   - Linux
8. **Distribution Method**: GitHub releases, personal website, or other?

---

## License & Distribution
- Recommended: MIT License (if open source)
- Keep API keys secure (never commit to git)
- Consider adding anonymization feature if sharing the tool