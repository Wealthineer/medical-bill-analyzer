# Phase 2: Enhanced Analytics - Detailed Tasks

**Status**: 🔄 Not Started
**Estimated Duration**: Week 3
**Dependencies**: Phase 1 must be complete

---

## Overview

Phase 2 adds analytics capabilities to understand spending patterns by practitioner, category, and time. **No database schema changes required** - builds entirely on existing bills table from Phase 1.

---

## 2.1 Analytics Module Setup

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/analytics/__init__.py`
- [ ] `src/medical_bill_analyzer/analytics/practitioner_stats.py`
- [ ] `src/medical_bill_analyzer/analytics/category_stats.py`
- [ ] `src/medical_bill_analyzer/analytics/time_series.py`
- [ ] `src/medical_bill_analyzer/analytics/formatters.py`

### Dependencies to Add:
- [ ] Add `plotille = "^5.0.0"` to pyproject.toml (optional, can use Rich instead)

### Tasks:
- [ ] Create analytics module structure
- [ ] Set up shared analytics utilities
- [ ] Create base analytics classes/types

---

## 2.2 Practitioner Statistics

**Status**: 🔄 Pending

### Tasks:
- [ ] Implement PractitionerStats class
- [ ] calculate() method - group by practitioner_name
- [ ] Create PractitionerSummary Pydantic model
- [ ] Calculate per practitioner: total, count, average, date range
- [ ] Sort by total spending (descending)
- [ ] Support year filtering

### SQL Query:
```sql
SELECT
    practitioner_name,
    COUNT(*) as visit_count,
    SUM(total_amount) as total_spent,
    AVG(total_amount) as average_per_visit,
    MIN(bill_date) as first_visit,
    MAX(bill_date) as last_visit
FROM bills
WHERE bill_date >= ? AND bill_date <= ?
GROUP BY practitioner_name
ORDER BY total_spent DESC
```

### Testing:
- [ ] Test with known test data
- [ ] Test year filtering
- [ ] Test with no data
- [ ] Test with single practitioner

---

## 2.3 Category Statistics

**Status**: 🔄 Pending

### Tasks:
- [ ] Implement CategoryStats class
- [ ] calculate() method - group by practitioner_type
- [ ] Create CategorySummary Pydantic model
- [ ] Calculate: total, count, percentage, average
- [ ] Support year filtering

### Key Metrics:
- Total amount per category
- Number of bills per category
- Percentage of total spending
- Average per bill in category

### Testing:
- [ ] Test category aggregation
- [ ] Test percentage calculations
- [ ] Test with all same category
- [ ] Test with missing categories

---

## 2.4 Time-Series Analysis

**Status**: 🔄 Pending

### Tasks:
- [ ] Implement TimeSeriesAnalysis class
- [ ] monthly_breakdown() method
- [ ] quarterly_breakdown() method
- [ ] year_over_year() comparison
- [ ] Create MonthSummary, QuarterSummary models

### SQL Query (Monthly):
```sql
SELECT
    strftime('%Y', bill_date) as year,
    strftime('%m', bill_date) as month,
    COUNT(*) as count,
    SUM(total_amount) as total,
    AVG(total_amount) as average
FROM bills
WHERE bill_date >= ? AND bill_date <= ?
GROUP BY year, month
ORDER BY year, month
```

### Testing:
- [ ] Test monthly aggregation
- [ ] Test quarterly aggregation
- [ ] Test year-over-year comparison
- [ ] Test with sparse data (missing months)

---

## 2.5 CLI Commands - Phase 2

**Status**: 🔄 Pending

### Files to Create:
- [ ] `src/medical_bill_analyzer/cli/stats_cmd.py`
- [ ] `src/medical_bill_analyzer/cli/practitioner_cmd.py`

### `stats` Command:
- [ ] Implement stats command with Typer
- [ ] `--by practitioner` option
- [ ] `--by category` option
- [ ] `--by month` option
- [ ] `--year` filter
- [ ] `--top N` limit

### `practitioner` Command:
- [ ] Implement practitioner command
- [ ] Show details for specific practitioner (by name)
- [ ] `--list` option to list all practitioners
- [ ] Display all bills, total, average, history

### Testing:
- [ ] Test stats command with various options
- [ ] Test practitioner command
- [ ] Test filtering and sorting
- [ ] Test error handling

---

## 2.6 Output Enhancements with Charts

**Status**: 🔄 Pending

### Files to Update:
- [ ] `src/medical_bill_analyzer/analytics/formatters.py`

### Tasks:
- [ ] Implement format_practitioner_table() using Rich Table
- [ ] Implement format_category_chart() with bar chart
- [ ] Implement format_time_series() with ASCII line chart
- [ ] Create percentage bars (████████░░ 80%)
- [ ] Add color coding (Rich colors)

### Visualization Examples:
```
Category Breakdown:
Arzt        ████████████░░░░░░░░ 60% (€600.00)
Zahnarzt    ██████░░░░░░░░░░░░░░ 30% (€300.00)
Labor       ██░░░░░░░░░░░░░░░░░░ 10% (€100.00)
```

### Testing:
- [ ] Test table formatting
- [ ] Test chart generation
- [ ] Test with various data sizes
- [ ] Test color output

---

## 2.7 Testing for Analytics

**Status**: 🔄 Pending

### Files to Create:
- [ ] `tests/unit/test_analytics/test_practitioner_stats.py`
- [ ] `tests/unit/test_analytics/test_category_stats.py`
- [ ] `tests/unit/test_analytics/test_time_series.py`
- [ ] `tests/unit/test_analytics/test_formatters.py`
- [ ] `tests/integration/test_analytics_commands.py`

### Tasks:
- [ ] Create test fixtures with known data
- [ ] Test all analytics calculations
- [ ] Test grouping and aggregation
- [ ] Test filtering by year
- [ ] Test edge cases (no data, single record)
- [ ] Test output formatting
- [ ] **Regression Tests**: Ensure Phase 1 commands still work

### Regression Testing:
- [ ] Run all Phase 1 tests to ensure no breaking changes
- [ ] Test Phase 1 commands: setup, add, list, total, bonus-check
- [ ] Verify Phase 1 functionality unchanged

---

## Phase 2 Acceptance Criteria

- [ ] ✅ Can generate practitioner-level spending report
- [ ] ✅ Can generate category-level spending report
- [ ] ✅ Can show monthly/quarterly spending trends
- [ ] ✅ Can identify top N spending practitioners
- [ ] ✅ Visual output is clear and actionable
- [ ] ✅ **Phase 1 functionality remains unchanged** (regression tests pass)

---

## Notes

- **No Database Changes**: Phase 2 uses only the existing bills table
- **Backward Compatible**: All Phase 1 functionality must continue working
- **Dependencies**: Requires Phase 1 complete (bills table populated with data)
- **Performance**: Consider indexing if queries are slow with large datasets
- **Future**: Phase 3 will add line_items table, but doesn't affect Phase 2

---

Last Updated: 2025-12-12
