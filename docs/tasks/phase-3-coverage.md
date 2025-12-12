# Phase 3: Line Items & Coverage Analysis - Detailed Tasks

**Status**: 🔄 Not Started
**Estimated Duration**: Weeks 4-5
**Dependencies**: Phase 1 & 2 must be complete

---

## Overview

Phase 3 extracts individual line items from bills (GOÄ codes, quantities, prices) and compares against insurance contract coverage rules. This is a major enhancement requiring database schema extension.

**Important**: This phase extends the database but maintains backward compatibility with Phase 1 & 2.

---

## 3.1 Database Schema Extension

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/database/migrations/v2_line_items.sql`
- [ ] `src/medical_bill_analyzer/database/repositories/line_item_repository.py`
- [ ] `src/medical_bill_analyzer/database/repositories/coverage_repository.py`

### Tasks:
- [ ] Write v2_line_items.sql migration
- [ ] Update migration_manager.py to handle v2
- [ ] Test migration on existing Phase 1 database
- [ ] Implement LineItemRepository
- [ ] Implement CoverageRepository
- [ ] Update database models

### New Tables Schema:
```sql
CREATE TABLE IF NOT EXISTS line_items (
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

CREATE TABLE IF NOT EXISTS contract_coverage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goa_code TEXT UNIQUE,
    description TEXT,
    max_factor DECIMAL(3,2),
    coverage_percentage INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Testing:
- [ ] Test v2 migration application
- [ ] Test backward compatibility (Phase 1 extraction still works)
- [ ] Test line item CRUD operations
- [ ] Test coverage rule CRUD operations

---

## 3.2 Enhanced LLM Extraction for Line Items

**Status**: 🔄 Pending

### Files to Update:
- [ ] `src/medical_bill_analyzer/llm/prompts.py`
- [ ] `src/medical_bill_analyzer/llm/schemas.py`
- [ ] `src/medical_bill_analyzer/config/settings.py`

### Tasks:
- [ ] Create LINE_ITEM_EXTRACTION_PROMPT
- [ ] Create LineItem Pydantic model
- [ ] Create LineItemExtractionResponse model
- [ ] Add extract_line_items flag to config
- [ ] Update BillExtractor to handle line items
- [ ] Conditional prompt selection (basic vs. line items)

### Prompt Structure:
Extract from bills:
- Practitioner info (same as Phase 1)
- Line items array with: position, date, goa_code, description, quantity, unit_price, total_price, factor

### Configuration:
```yaml
extraction:
  retry_attempts: 1
  extract_line_items: false  # Set to true to enable
```

### Testing:
- [ ] Test line item extraction with mock LLM
- [ ] Test with Phase 1 prompt still works (extract_line_items: false)
- [ ] Test parsing of line items array
- [ ] Test validation of GOÄ codes

---

## 3.3 Coverage Analysis Module

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/coverage/__init__.py`
- [ ] `src/medical_bill_analyzer/coverage/analyzer.py`
- [ ] `src/medical_bill_analyzer/coverage/matcher.py`
- [ ] `src/medical_bill_analyzer/coverage/reporter.py`

### Tasks:
- [ ] Implement CoverageMatcher class
- [ ] Implement CoverageAnalyzer class
- [ ] Calculate coverage for line items
- [ ] Detect factor violations
- [ ] Implement coverage report generation
- [ ] Create LineItemCoverage and CoverageReport models

### Coverage Calculation Logic:
1. Match line item to coverage rule by GOÄ code
2. If no rule: status = "unknown"
3. If coverage_percentage = 0: status = "not_covered"
4. If factor > max_factor: status = "partially_covered" (factor violation)
5. Else: calculate covered_amount based on percentage

### Testing:
- [ ] Test coverage matching
- [ ] Test coverage calculations
- [ ] Test factor violation detection
- [ ] Test with no coverage rules
- [ ] Test with all covered/not covered

---

## 3.4 CLI Commands - Phase 3

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/cli/line_items_cmd.py`
- [ ] `src/medical_bill_analyzer/cli/coverage_cmd.py`
- [ ] `src/medical_bill_analyzer/cli/reprocess_cmd.py`

### Commands to Implement:

#### `line-items` Command:
- [ ] Show line items for specific bill (`--bill-id`)
- [ ] Show line items for date range (`--from`, `--to`)
- [ ] Filter by GOÄ code (`--goa`)
- [ ] Show top N common/expensive procedures (`--top`)

#### `coverage` Command (with subcommands):
- [ ] `coverage add` - Manually add coverage rule
- [ ] `coverage import` - Import from CSV
- [ ] `coverage list` - List all coverage rules
- [ ] `coverage check` - Check coverage for specific bill
- [ ] `coverage report` - Generate full coverage report

#### `reprocess` Command:
- [ ] Reprocess specific bill (`--bill-id`)
- [ ] Reprocess all bills (`--all`)
- [ ] Enable line item extraction (`--extract-line-items`)

### CSV Import Format:
```csv
goa_code,description,max_factor,coverage_percentage
1,Beratung,2.3,100
5,Symptombezogene Untersuchung,2.3,100
250,Blutentnahme,1.8,80
```

### Testing:
- [ ] Test line-items command with various filters
- [ ] Test coverage add/import/list commands
- [ ] Test CSV import with valid/invalid data
- [ ] Test reprocessing workflow
- [ ] Test error handling

---

## 3.5 Coverage Reports

**Status**: 🔄 Pending

### Tasks:
- [ ] Implement format_coverage_report()
- [ ] Display total billed vs. covered
- [ ] Show breakdown by coverage status
- [ ] List top non-covered items
- [ ] List factor violations
- [ ] Use Rich Panel for formatted output

### Report Format:
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
2. GOÄ 5855 - Ultrasound (Factor 3.5) - €65.00 (Exceeds max 2.3)
...

Factor Violations:
- GOÄ 5855: Charged 3.5x, Contract max 2.3x (€40.00 excess)
```

### Testing:
- [ ] Test report generation with known data
- [ ] Test with no coverage rules
- [ ] Test with all covered/not covered
- [ ] Test formatting and colors

---

## 3.6 Testing for Coverage Analysis

**Status**: 🔄 Pending

### Files to Create:
- [ ] `tests/unit/test_coverage/test_matcher.py`
- [ ] `tests/unit/test_coverage/test_analyzer.py`
- [ ] `tests/unit/test_coverage/test_reporter.py`
- [ ] `tests/unit/test_database/test_line_item_repository.py`
- [ ] `tests/unit/test_database/test_coverage_repository.py`
- [ ] `tests/integration/test_coverage_workflow.py`

### Tasks:
- [ ] Test line item extraction
- [ ] Test coverage matching
- [ ] Test coverage calculations
- [ ] Test CSV import
- [ ] Test reprocessing
- [ ] Test database migration
- [ ] **Regression Tests**: Ensure Phase 1 & 2 still work

### Regression Testing:
- [ ] Run all Phase 1 tests
- [ ] Run all Phase 2 tests
- [ ] Test Phase 1 commands with Phase 3 database
- [ ] Test Phase 2 analytics with Phase 3 database
- [ ] Verify no breaking changes

---

## Phase 3 Acceptance Criteria

- [ ] ✅ Can extract line items from bills (GOÄ codes, descriptions, amounts, factors)
- [ ] ✅ Can store and manage contract coverage rules
- [ ] ✅ Can calculate coverage for individual line items
- [ ] ✅ Can generate comprehensive coverage analysis report
- [ ] ✅ Can identify most expensive non-covered items
- [ ] ✅ Can detect and flag factor violations (charged > contract max)
- [ ] ✅ Can import coverage rules from CSV
- [ ] ✅ Can reprocess existing bills with line item extraction
- [ ] ✅ **Phase 1 and Phase 2 functionality unchanged** (backward compatible)

---

## Notes

- **Database Migration**: Critical to test migration on existing Phase 1 database
- **Backward Compatibility**: `extract_line_items: false` maintains Phase 1 behavior
- **Performance**: Line item extraction may be slower (more tokens)
- **Accuracy**: LLM may struggle with complex bill formats
- **Future**: Can enhance prompts iteratively based on real bills

---

Last Updated: 2025-12-12
