# Phase 1: Core Functionality - Detailed Tasks

**Status**: In Progress (30% complete)
**Estimated Duration**: Weeks 1-2
**Dependencies**: None (this is the foundation)

---

## 1.1 Project Infrastructure Setup ✅ COMPLETED

**Status**: ✅ Done

### Files Created:
- [x] `.gitignore` - Python, IDE, data files
- [x] `pyproject.toml` - Dependencies and project config
- [x] `README.md` - Project overview
- [x] `LICENSE` - MIT License
- [x] `.env.example` - Environment variables template
- [x] `config.yaml.template` - Configuration template

### Tasks:
- [x] Initialize git repository
- [x] Create directory structure (src/, tests/, docs/, data/, etc.)
- [x] Add all core dependencies to pyproject.toml
- [x] Add development dependencies (pytest, black, ruff, mypy)
- [x] Create initial README with installation instructions

**Commit**: `23f6374` - "Add configuration management module with Pydantic settings"

---

## 1.2 Configuration Management ✅ COMPLETED

**Status**: ✅ Done

### Files Created:
- [x] `src/medical_bill_analyzer/__init__.py`
- [x] `src/medical_bill_analyzer/config/__init__.py`
- [x] `src/medical_bill_analyzer/config/settings.py`
- [x] `src/medical_bill_analyzer/config/defaults.py`

### Tasks:
- [x] Create Settings class with Pydantic
- [x] Support for Anthropic, OpenAI, Ollama configs
- [x] YAML configuration loading/saving
- [x] Environment variable support
- [x] User directory detection (cross-platform)
- [x] First-run detection (is_first_run())
- [x] get_settings() and save_settings() functions

### Key Features:
- ✅ Type-safe configuration with Pydantic
- ✅ Multiple LLM provider support
- ✅ Automatic path resolution (user config directory)
- ✅ Environment variable override capability

**Commit**: `23f6374` - "Add configuration management module with Pydantic settings"

---

## 1.3 Utilities and Logging ✅ COMPLETED

**Status**: ✅ Done | ✅ Tested (99 tests, 88% coverage)

### Files Created:
- [x] `src/medical_bill_analyzer/core/exceptions.py`
- [x] `src/medical_bill_analyzer/core/__init__.py`
- [x] `src/medical_bill_analyzer/utils/__init__.py`
- [x] `src/medical_bill_analyzer/utils/logger.py`
- [x] `src/medical_bill_analyzer/utils/file_utils.py`
- [x] `src/medical_bill_analyzer/utils/date_utils.py`
- [x] `src/medical_bill_analyzer/utils/currency_utils.py`
- [x] `src/medical_bill_analyzer/utils/validation.py`

### Tasks:
- [x] Create custom exception hierarchy
- [x] Logger with file and console output
- [x] File utilities (hashing, sanitization, copying)
- [x] Date parsing for German formats (DD.MM.YYYY)
- [x] Currency formatting/parsing (EUR)
- [x] Validation functions (amount, date, practitioner type)

### Key Features:
- ✅ SHA256 file hashing for duplicate detection
- ✅ German date format support (DD.MM.YYYY)
- ✅ EUR currency formatting (1.234,56 €)
- ✅ Comprehensive validation utilities
- ✅ Structured logging to file and console

**Commit**: `d47c06b` - "Add utilities module and custom exceptions"

### Testing Status ✅:
- [x] Configuration tests (15 tests, 91-100% coverage)
- [x] File utilities tests (17 tests, 96% coverage)
- [x] Date utilities tests (18 tests, 100% coverage)
- [x] Currency utilities tests (21 tests, 95% coverage)
- [x] Validation tests (18 tests, 93% coverage)
- [x] Exception tests (10 tests, 100% coverage)
- [ ] Logger tests (deferred - not critical for MVP)

**Total**: 99 tests passing, 88% overall coverage

**Commit**: `f9d6174` - "Add comprehensive automated tests for Phase 1.1-1.3"

---

## 1.4 Database Layer ✅ COMPLETED

**Status**: ✅ Done

### Files Created:
- [x] `src/medical_bill_analyzer/database/__init__.py`
- [x] `src/medical_bill_analyzer/database/connection.py`
- [x] `src/medical_bill_analyzer/database/schema.py`
- [x] `src/medical_bill_analyzer/database/models.py`
- [x] `src/medical_bill_analyzer/database/repositories/__init__.py`
- [x] `src/medical_bill_analyzer/database/repositories/base.py`
- [x] `src/medical_bill_analyzer/database/repositories/bill_repository.py`
- [x] `src/medical_bill_analyzer/database/migrations/__init__.py`
- [x] `src/medical_bill_analyzer/database/migrations/v1_initial.sql`
- [x] `src/medical_bill_analyzer/database/migrations/migration_manager.py`

### Tasks:
- [x] Create SQLite connection manager with context managers
- [x] Define bills table schema (see SQL below)
- [x] Create Pydantic models (Bill, BillCreate, BillUpdate, BillFilter)
- [x] Implement base repository class with CRUD operations
- [x] Implement BillRepository with specialized queries
- [x] Create migration manager for schema versioning
- [x] Write v1_initial.sql migration
- [x] Add Decimal type adapter/converter for currency handling

### Database Schema (v1_initial.sql):
```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,
    pdf_path TEXT NOT NULL,
    practitioner_name TEXT,
    practitioner_type TEXT,
    bill_date DATE,
    bill_number TEXT,
    total_amount DECIMAL(10,2),
    currency TEXT DEFAULT 'EUR',
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_status TEXT DEFAULT 'success',
    raw_extraction_json TEXT,
    notes TEXT
);

CREATE INDEX idx_bill_date ON bills(bill_date);
CREATE INDEX idx_practitioner_name ON bills(practitioner_name);
CREATE INDEX idx_practitioner_type ON bills(practitioner_type);
CREATE INDEX idx_file_hash ON bills(file_hash);
```

### Key Repository Methods:
- [x] `create(bill: BillCreate) -> Bill`
- [x] `get_by_id(id: int) -> Bill | None`
- [x] `get_by_filename(filename: str) -> Bill | None`
- [x] `get_by_date_range(start: date, end: date) -> List[Bill]`
- [x] `get_by_year(year: int) -> List[Bill]`
- [x] `check_duplicate_hash(file_hash: str) -> bool`
- [x] `get_by_status(status: str) -> List[Bill]`
- [x] `filter(criteria: BillFilter) -> List[Bill]`
- [x] `update(id: int, updates: BillUpdate) -> Bill`
- [x] `delete(id: int) -> bool`
- [x] `get_total_amount(...) -> Decimal`
- [x] `count(filter: BillFilter) -> int`

### Key Features:
- ✅ SQLite connection management with context managers
- ✅ Decimal type support for accurate currency handling
- ✅ Migration system for schema versioning
- ✅ Repository pattern for clean data access
- ✅ Type-safe Pydantic models
- ✅ Duplicate detection by file hash and filename
- ✅ Flexible filtering by date, practitioner, status, amount
- ✅ Foreign key support and indexed queries

### Testing:
- [x] Manual integration test (verified all operations work)
- [ ] Automated unit tests (Phase 1.10)

**Commit**: `0c0f897` - "Add Phase 1.4: Database layer with SQLite and repository pattern"

---

## 1.5 PDF Processing Pipeline

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/pdf/__init__.py`
- [ ] `src/medical_bill_analyzer/pdf/extractor.py`
- [ ] `src/medical_bill_analyzer/pdf/validator.py`
- [ ] `src/medical_bill_analyzer/pdf/utils.py`

### Tasks:
- [ ] Implement PDF text extraction with pdfplumber
- [ ] Handle multi-page PDFs
- [ ] Detect corrupted PDFs
- [ ] Detect scanned PDFs (no text layer)
- [ ] Handle password-protected PDFs gracefully
- [ ] File hash calculation integration

### Key Functions:
- [ ] `extract_text_from_pdf(pdf_path: Path) -> str`
- [ ] `validate_pdf(pdf_path: Path) -> ValidationResult`
- [ ] `is_scanned_pdf(pdf_path: Path) -> bool`

### Testing:
- [ ] Test text extraction from valid multi-page PDF
- [ ] Test handling of corrupted PDF
- [ ] Test detection of scanned PDF
- [ ] Test file hash consistency

---

## 1.6 LLM Provider Abstraction Layer

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/llm/__init__.py`
- [ ] `src/medical_bill_analyzer/llm/base.py`
- [ ] `src/medical_bill_analyzer/llm/anthropic_provider.py`
- [ ] `src/medical_bill_analyzer/llm/openai_provider.py`
- [ ] `src/medical_bill_analyzer/llm/ollama_provider.py`
- [ ] `src/medical_bill_analyzer/llm/factory.py`
- [ ] `src/medical_bill_analyzer/llm/prompts.py`
- [ ] `src/medical_bill_analyzer/llm/schemas.py`

### Tasks:
- [ ] Define abstract LLMProvider base class
- [ ] Implement AnthropicProvider (Claude)
- [ ] Implement OpenAIProvider (GPT)
- [ ] Implement OllamaProvider (local)
- [ ] Create provider factory
- [ ] Write BASIC_EXTRACTION_PROMPT
- [ ] Define BasicExtractionResponse schema with Pydantic

### Abstract Interface:
```python
class LLMProvider(ABC):
    @abstractmethod
    def extract(self, bill_text: str, extraction_type: str = "basic") -> dict:
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        pass
```

### Prompt Template (Phase 1 - Basic):
Extract: practitioner_name, practitioner_type, bill_date, bill_number, total_amount, currency

### Testing:
- [ ] Test each provider with mock responses
- [ ] Test provider factory selection
- [ ] Test error handling (API failures, invalid responses)
- [ ] Test retry logic

---

## 1.7 Information Extraction Pipeline

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/extraction/__init__.py`
- [ ] `src/medical_bill_analyzer/extraction/bill_extractor.py`
- [ ] `src/medical_bill_analyzer/extraction/parser.py`
- [ ] `src/medical_bill_analyzer/extraction/validator.py`
- [ ] `src/medical_bill_analyzer/extraction/retry.py`

### Tasks:
- [ ] Create BillExtractor orchestration class
- [ ] Implement JSON response parser (handle markdown blocks)
- [ ] Implement extracted data validator
- [ ] Implement retry logic with exponential backoff
- [ ] Create ExtractionResult class

### Workflow:
1. Validate PDF
2. Extract text from PDF
3. Send to LLM provider (with retry)
4. Parse JSON response
5. Validate extracted data
6. Return ExtractionResult

### Testing:
- [ ] Test end-to-end extraction with mock LLM
- [ ] Test malformed JSON handling
- [ ] Test validation rejection (negative amount, future date)
- [ ] Test retry on API failure

---

## 1.8 Core Business Logic

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/core/bill_processor.py`
- [ ] `src/medical_bill_analyzer/core/bonus_calculator.py`

### Tasks:
- [ ] Implement BillProcessor class
- [ ] process_single_bill() method
- [ ] process_multiple_bills() with progress tracking
- [ ] Implement BonusCalculator class
- [ ] calculate_total() method
- [ ] compare_to_threshold() method
- [ ] Create ProcessingResult and BonusRecommendation classes

### Key Features:
- [ ] Duplicate detection during processing
- [ ] Batch processing with progress bars
- [ ] Clear bonus recommendations
- [ ] Copy PDFs to storage directory

### Testing:
- [ ] Test single bill processing
- [ ] Test batch processing
- [ ] Test duplicate handling
- [ ] Test bonus recommendation logic

---

## 1.9 CLI Commands

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/__main__.py`
- [ ] `src/medical_bill_analyzer/main.py`
- [ ] `src/medical_bill_analyzer/cli/__init__.py`
- [ ] `src/medical_bill_analyzer/cli/app.py`
- [ ] `src/medical_bill_analyzer/cli/setup_cmd.py`
- [ ] `src/medical_bill_analyzer/cli/add_cmd.py`
- [ ] `src/medical_bill_analyzer/cli/list_cmd.py`
- [ ] `src/medical_bill_analyzer/cli/total_cmd.py`
- [ ] `src/medical_bill_analyzer/cli/bonus_cmd.py`
- [ ] `src/medical_bill_analyzer/cli/utils.py`

### Commands to Implement:
- [ ] `setup` - Interactive wizard for first-run configuration
- [ ] `add` - Add single bill or batch of bills
- [ ] `list` - List bills with filtering
- [ ] `total` - Calculate total costs
- [ ] `bonus-check` - Compare against bonus threshold

### Setup Wizard Flow:
1. Welcome message and privacy notice
2. LLM provider selection (Anthropic/OpenAI/Ollama)
3. API key input (masked)
4. Connection test
5. Bonus threshold setting
6. Database initialization
7. Config file creation

### Testing:
- [ ] Test each command with various inputs
- [ ] Test interactive prompts
- [ ] Test error handling
- [ ] Test output formatting

---

## 1.10 Documentation and Testing

**Status**: 🔄 Pending

### Files to Create:
- [ ] `tests/conftest.py`
- [ ] `tests/unit/test_llm/test_providers.py`
- [ ] `tests/unit/test_pdf/test_extractor.py`
- [ ] `tests/unit/test_extraction/test_bill_extractor.py`
- [ ] `tests/unit/test_database/test_repositories.py`
- [ ] `tests/integration/test_bill_processing.py`
- [ ] `tests/integration/test_cli_commands.py`
- [ ] `docs/installation.md`
- [ ] `docs/user_guide.md`
- [ ] `docs/development.md`

### Tasks:
- [ ] Create pytest fixtures (test_db, mock_llm_provider, sample_pdf)
- [ ] Write unit tests for all modules (>80% coverage)
- [ ] Write integration tests for workflows
- [ ] Create 3-5 anonymized sample German medical bills
- [ ] Mock LLM responses (save JSON fixtures)
- [ ] Write installation guide
- [ ] Write user guide with command examples
- [ ] Write development guide
- [ ] Add docstrings to all public functions

### Testing Goals:
- [ ] Coverage >80% for core modules
- [ ] All error paths tested
- [ ] Mock LLM calls (no API costs in tests)
- [ ] Test with sample German medical bills

---

## Phase 1 Acceptance Criteria

- [ ] ✅ Setup wizard completes for all 3 LLM providers (Anthropic, OpenAI, Ollama)
- [ ] ✅ Can process a single PDF and extract basic information
- [ ] ✅ Can batch process multiple PDFs from directory
- [ ] ✅ Duplicate PDFs detected by file hash and skipped
- [ ] ✅ Total costs can be calculated for any date range
- [ ] ✅ Bonus recommendation provides clear, actionable output
- [ ] ✅ All data stored locally in SQLite database
- [ ] ✅ Test coverage >80% for core modules
- [ ] ✅ User documentation complete (installation, user guide)

---

## Notes

- **Dependencies**: Phase 1 must be fully complete before Phase 2 can start
- **Critical Path**: LLM provider abstraction → Extraction pipeline → CLI commands
- **Risk**: LLM extraction accuracy with varied German bill formats
- **Mitigation**: Store raw_extraction_json for debugging, allow manual review

---

Last Updated: 2025-12-12
