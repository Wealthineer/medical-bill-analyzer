# Phase 4a: Text User Interface - Detailed Tasks

**Status**: 🔄 Not Started
**Estimated Duration**: Weeks 6-7
**Dependencies**: Phase 1, 2, 3 must be complete

---

## Overview

Phase 4a creates an interactive terminal UI using Textual framework. The TUI wraps existing business logic without duplicating code - it's a presentation layer only.

**Key Principle**: TUI screens call the same core modules (bill_processor, analytics, coverage) as the CLI commands.

---

## 4a.1 TUI Framework Setup

**Status**: 🔄 Pending

### Dependencies to Add:
- [ ] Add `textual = "^0.86.0"` to pyproject.toml

### Files to Create:
- [ ] `src/medical_bill_analyzer/tui/__init__.py`
- [ ] `src/medical_bill_analyzer/tui/app.py`

### Tasks:
- [ ] Create main TUI application class
- [ ] Define global keyboard shortcuts
- [ ] Set up CSS styling (optional)
- [ ] Configure header and footer
- [ ] Implement main event loop

### Global Shortcuts:
- [ ] `q` - Quit
- [ ] `a` - Add bills
- [ ] `s` - Statistics
- [ ] `c` - Coverage
- [ ] `?` - Help
- [ ] `/` - Search
- [ ] `r` - Refresh

### Testing:
- [ ] Test TUI launches
- [ ] Test keyboard shortcuts
- [ ] Test graceful exit

---

## 4a.2 Dashboard Screen

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/tui/screens/__init__.py`
- [ ] `src/medical_bill_analyzer/tui/screens/dashboard.py`

### Tasks:
- [ ] Create Dashboard screen class
- [ ] Display 2024 summary (total bills, total cost)
- [ ] Show bonus threshold status
- [ ] Display recent bills table (last 10)
- [ ] Color-code status indicators
- [ ] Implement data loading from repositories

### Layout:
```
┌─ Medical Bill Analyzer ────────────────────────┐
│                                                 │
│  📊 2024 Summary                                │
│  ───────────────────────────────────────────── │
│  Total Bills: 23        Total Cost: €2,450.00  │
│  Bonus Threshold: €1,000.00  ⚠️ OVER THRESHOLD │
│                                                 │
│  📁 Recent Bills                                │
│  ┌──────────┬─────────────────┬─────────────┐  │
│  │ Date     │ Practitioner    │ Amount      │  │
│  ├──────────┼─────────────────┼─────────────┤  │
│  │ 01.12.24 │ Dr. Schmidt     │ €120.00     │  │
│  └──────────┴─────────────────┴─────────────┘  │
│                                                 │
│  [A]dd Bills  [S]tats  [C]overage  [Q]uit     │
└─────────────────────────────────────────────────┘
```

### Testing:
- [ ] Test data loading
- [ ] Test table display
- [ ] Test status indicators
- [ ] Test navigation

---

## 4a.3 Navigation System

**Status**: 🔄 Pending

### Tasks:
- [ ] Implement screen stack (push/pop screens)
- [ ] Handle back navigation (Esc key)
- [ ] Implement screen transitions
- [ ] Create breadcrumb navigation
- [ ] Handle modal dialogs

### Navigation Flow:
- Dashboard → (Stats/Bills/Coverage/Add Wizard)
- Each screen → Back to Dashboard
- Modal dialogs → Overlay current screen

### Testing:
- [ ] Test screen transitions
- [ ] Test back navigation
- [ ] Test deep navigation
- [ ] Test modal handling

---

## 4a.4 Statistics Screen

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/tui/screens/stats.py`

### Tasks:
- [ ] Create tabbed statistics view
- [ ] Tab 1: Practitioner statistics
- [ ] Tab 2: Category statistics
- [ ] Tab 3: Monthly trend
- [ ] Call analytics module (reuse Phase 2 code)
- [ ] Display charts/tables
- [ ] Implement refresh

### Layout:
```
┌─ Statistics ────────────────────────────────────┐
│ [Practitioner] [Category] [Monthly]             │
│                                                  │
│  Practitioner Spending (2024)                   │
│  ──────────────────────────────────────────────│
│  Dr. Schmidt      ████████████░░ 45%  €450.00  │
│  Dr. Müller       ██████░░░░░░░ 30%  €300.00  │
│  Zahnarzt Weber   ████░░░░░░░░░ 25%  €250.00  │
│                                                  │
│  [R]efresh  [Esc] Back                          │
└──────────────────────────────────────────────────┘
```

### Testing:
- [ ] Test tab switching
- [ ] Test data loading from analytics module
- [ ] Test chart rendering
- [ ] Test refresh

---

## 4a.5 Bill Management Screen

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/tui/screens/bills.py`

### Tasks:
- [ ] Create bill list screen
- [ ] Implement sortable/filterable DataTable
- [ ] Add search functionality
- [ ] Detail view on selection
- [ ] Batch operations support
- [ ] Call BillRepository (reuse database layer)

### Features:
- [ ] Sort by: date, practitioner, amount
- [ ] Filter by: year, status, practitioner
- [ ] Search: practitioner name, bill number
- [ ] Actions: view details, edit notes, delete

### Testing:
- [ ] Test table display
- [ ] Test sorting
- [ ] Test filtering
- [ ] Test search
- [ ] Test detail view

---

## 4a.6 Add Bills Wizard

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/tui/screens/add_wizard.py`

### Tasks:
- [ ] Create multi-step wizard
- [ ] Step 1: File selection (path input)
- [ ] Step 2: Processing with progress bar
- [ ] Step 3: Review extracted data
- [ ] Step 4: Confirm and save
- [ ] Call BillProcessor (reuse core logic)

### Wizard Flow:
1. **File Selection**: Input path to PDF or directory
2. **Processing**: Show progress bar, extraction status
3. **Review**: Display extracted data, flag issues
4. **Confirm**: Save to database, show summary

### Testing:
- [ ] Test wizard flow
- [ ] Test file selection
- [ ] Test progress display
- [ ] Test error handling
- [ ] Test review and confirm

---

## 4a.7 Coverage Analysis Screen

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/tui/screens/coverage.py`

### Tasks:
- [ ] Create coverage analysis screen
- [ ] Display coverage report
- [ ] Show visual breakdown (bar chart)
- [ ] List non-covered items
- [ ] List factor violations
- [ ] Call CoverageAnalyzer (reuse Phase 3 code)

### Layout:
```
┌─ Coverage Analysis (2024) ──────────────────────┐
│                                                  │
│  Total Billed:    €2,450.00                     │
│  Total Covered:   €2,100.00 (85.7%)             │
│  Not Covered:     €350.00 (14.3%)               │
│                                                  │
│  [█████████████████░░░░] 85.7% Covered          │
│                                                  │
│  Top Non-Covered Items:                         │
│  1. GOÄ 3500 - Alternative Medicine - €80.00    │
│  2. GOÄ 5855 - Ultrasound (Factor 3.5) - €65.00│
│                                                  │
│  [R]efresh  [Esc] Back                          │
└──────────────────────────────────────────────────┘
```

### Testing:
- [ ] Test coverage report display
- [ ] Test visual breakdown
- [ ] Test data loading
- [ ] Test refresh

---

## 4a.8 Keyboard Shortcuts

**Status**: 🔄 Pending

### Tasks:
- [ ] Implement global shortcuts (defined in 4a.1)
- [ ] Implement screen-specific shortcuts
- [ ] Create help screen listing all shortcuts
- [ ] Show shortcuts in footer
- [ ] Handle conflicts

### Shortcuts Summary:
- **Global**: q (quit), a (add), s (stats), c (coverage), ? (help)
- **Navigation**: Arrow keys, Enter, Esc, Tab
- **Actions**: r (refresh), / (search), e (edit)

### Testing:
- [ ] Test all global shortcuts
- [ ] Test screen-specific shortcuts
- [ ] Test help screen
- [ ] Test shortcut conflicts

---

## 4a.9 Custom Widgets

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/tui/widgets/__init__.py`
- [ ] `src/medical_bill_analyzer/tui/widgets/bill_table.py`
- [ ] `src/medical_bill_analyzer/tui/widgets/charts.py`

### Tasks:
- [ ] Create BillTable widget (custom DataTable)
- [ ] Create ASCIIBarChart widget
- [ ] Create PercentageBar widget
- [ ] Implement custom styling

### Widgets:
- **BillTable**: Sortable, filterable table for bills
- **ASCIIBarChart**: Text-based bar chart for statistics
- **PercentageBar**: Visual bar (████████░░ 80%)

### Testing:
- [ ] Test widget rendering
- [ ] Test widget interactions
- [ ] Test custom styling

---

## 4a.10 CLI Integration

**Status**: 🔄 Pending

### Files to Update:
- [ ] `src/medical_bill_analyzer/main.py`

### Tasks:
- [ ] Auto-launch TUI if no CLI arguments
- [ ] Check terminal support
- [ ] Fallback to CLI if TUI not available
- [ ] Add `--no-tui` flag
- [ ] Ensure CLI commands still work

### Launch Logic:
```python
if len(sys.argv) == 1 and sys.stdout.isatty():
    try:
        from tui.app import MedicalBillAnalyzerTUI
        app = MedicalBillAnalyzerTUI()
        app.run()
        return
    except ImportError:
        pass  # Fall back to CLI

# Use CLI
from cli.app import app
app()
```

### Testing:
- [ ] Test TUI auto-launch
- [ ] Test fallback to CLI
- [ ] Test --no-tui flag
- [ ] Test CLI commands still work
- [ ] Test on various terminals

---

## 4a.11 TUI Testing

**Status**: 🔄 Pending

### Files to Create:
- [ ] `tests/unit/test_tui/test_screens.py`
- [ ] `tests/unit/test_tui/test_widgets.py`
- [ ] `tests/integration/test_tui_workflow.py`

### Tasks:
- [ ] Use Textual testing utilities
- [ ] Test screen rendering
- [ ] Test navigation
- [ ] Test keyboard shortcuts
- [ ] Test data loading
- [ ] Test business logic calls
- [ ] **Regression Tests**: Phase 1-3 CLI still works

### Key Tests:
- [ ] TUI calls correct core modules (bill_processor, analytics, coverage)
- [ ] No business logic duplication in TUI
- [ ] CLI regression tests pass
- [ ] TUI gracefully degrades on unsupported terminals

---

## Phase 4a Acceptance Criteria

- [ ] ✅ TUI launches successfully and displays dashboard
- [ ] ✅ Can add bills through TUI wizard
- [ ] ✅ Can navigate all major screens with keyboard
- [ ] ✅ TUI gracefully degrades if terminal doesn't support rich features (falls back to CLI)
- [ ] ✅ All CLI functionality accessible through TUI
- [ ] ✅ TUI state persists (remembers last view, filters)
- [ ] ✅ **Phase 1-3 functionality unchanged** (TUI is additive)

---

## Notes

- **No Business Logic**: TUI only calls existing core modules
- **Presentation Layer**: TUI is UI only, all logic in core/analytics/coverage
- **Backward Compatible**: CLI commands must still work
- **Terminal Support**: Test on Windows CMD, PowerShell, Terminal.app, Linux terminals
- **Performance**: TUI should feel responsive, use async where appropriate

---

Last Updated: 2025-12-12
