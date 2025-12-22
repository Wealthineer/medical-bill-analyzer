# Testing Guide - Medical Bill Analyzer

This guide will walk you through testing the complete application end-to-end.

## Prerequisites

1. **Have your API key ready** (if using Anthropic or OpenAI):
   - Get an Anthropic API key from: https://console.anthropic.com
   - Or get an OpenAI API key from: https://platform.openai.com
   - The setup wizard will prompt you to enter it and save it securely to the database

2. **Have a German medical bill PDF ready** (or use one of the test PDFs):
   ```bash
   # Test PDFs are located here:
   ls tests/test_data/sample_bills/
   ```

## Step-by-Step Testing

### Step 1: Run Setup Wizard

```bash
python -m medical_bill_analyzer setup
```

**What to expect:**
- Welcome message and privacy notice
- Provider selection (1=Anthropic, 2=OpenAI, 3=Ollama)
- **API key prompt** (enter your API key when prompted - it will be saved securely to the database)
- Connection test with progress bar
- Bonus threshold prompt (default: 1000 EUR)
- Database initialization
- Credentials saved to database
- Config file saved to `~/.medical-bill-analyzer/config.yaml`

**Output should show:**
- ✓ Connected successfully
- ✓ Database initialized
- ✓ Credentials saved securely to database
- ✓ Configuration saved
- Next steps instructions

---

### Step 2: Add a Bill

```bash
# Add a single bill
python -m medical_bill_analyzer add tests/test_data/sample_bills/valid_bill.pdf

# OR add your own bill
python -m medical_bill_analyzer add /path/to/your/bill.pdf
```

**What to expect:**
- Progress bar: "Extracting and saving"
- Success message with extracted data:
  - Bill ID
  - Practitioner name
  - Bill date
  - Amount

**Example output:**
```
Processing: valid_bill.pdf
Extracting and saving ━━━━━━━━━━━━━━━━━━━━ 100%

✓ Bill added successfully!

  ID: 1
  Practitioner: Dr. Schmidt
  Date: 2024-01-15
  Amount: €150.50
```

---

### Step 3: Add Multiple Bills (Optional)

```bash
# Add all bills from a directory
python -m medical_bill_analyzer add tests/test_data/sample_bills/ --recursive
```

**What to expect:**
- Processing progress bar for each file
- Summary table showing:
  - Total files
  - Processed (green)
  - Skipped (yellow, e.g., duplicates)
  - Failed (red, if any)
  - Success rate

---

### Step 4: List Bills

```bash
# List all bills
python -m medical_bill_analyzer list

# Filter by year
python -m medical_bill_analyzer list --year 2024

# Filter by date range
python -m medical_bill_analyzer list --from 2024-01-01 --to 2024-12-31

# Filter by practitioner type
python -m medical_bill_analyzer list --type Zahnarzt
```

**What to expect:**
- Beautiful table with columns:
  - ID
  - Date
  - Practitioner
  - Type
  - Amount
  - Status (✓ = success)
- Summary: "Showing X bill(s)" and total amount

---

### Step 5: Calculate Total

```bash
# Total for all bills
python -m medical_bill_analyzer total

# Total for specific year
python -m medical_bill_analyzer total --year 2024

# Total for date range
python -m medical_bill_analyzer total --from 2024-01-01 --to 2024-12-31

# Total for specific practitioner type
python -m medical_bill_analyzer total --type Arzt
```

**What to expect:**
- Formatted box showing:
  - Filter context (year, period, or "All bills")
  - Total amount in EUR

**Example output:**
```
==================================================
Total Medical Costs
==================================================

Year: 2024

Total: €1,234.56

==================================================
```

---

### Step 6: Check Bonus Recommendation

```bash
# Check for current year with default threshold
python -m medical_bill_analyzer bonus-check

# Check for specific year
python -m medical_bill_analyzer bonus-check --year 2024

# Override threshold
python -m medical_bill_analyzer bonus-check --threshold 1500
```

**What to expect:**
- Formatted box showing:
  - Year
  - Your total medical costs
  - Bonus threshold
  - Difference
  - **Recommendation**: Keep Bonus OR Submit Claims (in green)
  - **Potential Savings** (in green, bold)
  - Detailed explanation

**Example output (costs below threshold):**
```
============================================================
Bonus Recommendation
============================================================

Year: 2024

Your Costs:
  Total medical costs: €750.00
  Bonus threshold:     €1,000.00
  Difference:          €-250.00

------------------------------------------------------------

✓ RECOMMENDATION: Keep Your Bonus

💰 Potential Savings: €250.00

------------------------------------------------------------

Explanation:
💰 Keep your bonus! Your medical costs (€750.00) are
€250.00 below your bonus threshold (€1,000.00).
By not submitting claims, you save €250.00.

============================================================
```

---

### Step 7: View Spending Statistics (Phase 2)

```bash
# Show all practitioners sorted by spending
python -m medical_bill_analyzer stats --by practitioner

# Show top 5 practitioners
python -m medical_bill_analyzer stats --by practitioner --top 5

# Category breakdown (Arzt, Zahnarzt, etc.)
python -m medical_bill_analyzer stats --by category

# Category breakdown for 2024 only
python -m medical_bill_analyzer stats --by category --year 2024

# Monthly trends for 2024
python -m medical_bill_analyzer stats --by month --year 2024

# Filter by practitioner type
python -m medical_bill_analyzer stats --by practitioner --type Zahnarzt
```

**What to expect with `--by practitioner`:**
- Rich table showing:
  - Practitioner name
  - Type (Arzt, Zahnarzt, etc.)
  - Number of visits
  - Total spending
  - Average per visit
  - Last visit date
- Practitioners sorted by total spending (highest first)
- Summary: Number of practitioners, total visits, combined total

**Example output:**
```
                    Practitioner Statistics
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Practitioner   ┃ Type     ┃ Visits ┃    Total ┃ Avg/Visit ┃ Last Visit ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Dr. Schmidt    │ Zahnarzt │      5 │  €500.00 │   €100.00 │ 2024-11-30 │
│ Dr. Müller     │ Arzt     │      3 │  €300.00 │   €100.00 │ 2024-09-20 │
│ Dr. Weber      │ Arzt     │      2 │  €150.00 │    €75.00 │ 2024-08-15 │
└────────────────┴──────────┴────────┴──────────┴───────────┴────────────┘

Showing 3 practitioner(s)
Total visits: 10
Combined total: €950.00
```

**What to expect with `--by category`:**
- Rich table showing:
  - Category/type (Arzt, Zahnarzt, etc.)
  - Number of bills
  - Total spending
  - Average per bill
  - Percentage of total spending
  - Visual percentage bar (█ = 5%)
- Categories with >20% spending marked with ★
- Summary: Number of categories, total bills, grand total

**Example output:**
```
                 Category Statistics - 2024
┏━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Category   ┃  Bills ┃    Total ┃ Avg/Bill  ┃ % of Total┃          ┃
┡━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ ★ Zahnarzt │      5 │  €500.00 │   €100.00 │      52.6%│ ██████████│
│ ★ Arzt     │      5 │  €450.00 │    €90.00 │      47.4%│ █████████ │
└────────────┴────────┴──────────┴───────────┴───────────┴──────────┘

★ = Major category (>20% of spending)

Showing 2 categories
Total bills: 10
Grand total: €950.00
```

**What to expect with `--by month`:**
- Rich table showing:
  - Period (YYYY-MM)
  - Month name (Jan, Feb, etc.)
  - Number of bills
  - Total spending
  - Average per bill
- Months sorted chronologically
- Summary: Number of months, total bills, average per month, total

**Example output:**
```
               Monthly Statistics - 2024
┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Period  ┃ Month ┃  Bills ┃    Total ┃ Avg/Bill  ┃
┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│ 2024-01 │ Jan   │      1 │  €100.00 │   €100.00 │
│ 2024-02 │ Feb   │      1 │   €90.00 │    €90.00 │
│ 2024-03 │ Mar   │      1 │  €120.00 │   €120.00 │
│ 2024-05 │ May   │      1 │  €110.00 │   €110.00 │
│ 2024-06 │ Jun   │      2 │  €155.00 │    €77.50 │
└─────────┴───────┴────────┴──────────┴───────────┘

Showing 5 months
Total bills: 6
Average per month: €115.00
Total: €575.00
```

---

## Testing Checklist

### Phase 1 - Core Functionality
- [ ] Setup wizard completes successfully
- [ ] Can add a single bill
- [ ] Extracted data looks correct (practitioner, date, amount)
- [ ] Can add multiple bills from directory
- [ ] Duplicate detection works (try adding same bill twice)
- [ ] List command shows bills in table
- [ ] Filtering works (year, date range, type)
- [ ] Total command calculates correctly
- [ ] Bonus recommendation shows correct decision
- [ ] All commands show colored output
- [ ] Help works for all commands

### Phase 2 - Enhanced Analytics
- [ ] Stats command shows practitioner breakdown
- [ ] Practitioners sorted by total spending (highest first)
- [ ] `--top N` flag limits results correctly
- [ ] Stats command shows category breakdown
- [ ] Categories show percentage bars
- [ ] Major categories (>20%) marked with ★
- [ ] Stats command shows monthly trends
- [ ] Months sorted chronologically
- [ ] `--year` filter works for all stat types
- [ ] `--type` filter works for practitioners and monthly stats
- [ ] Summary statistics shown for each view
- [ ] Rich tables display correctly with colors

---

## Troubleshooting

### Phase 1 Issues

#### "Configuration error"
- Run `python -m medical_bill_analyzer setup` first

#### "API key not found" or "Connection failed"
- The setup wizard should have prompted you to enter your API key
- Your API key is saved securely in the database (`~/.medical-bill-analyzer/data/medical_bills.db`)
- If you need to update it, run the setup wizard again:
  ```bash
  python -m medical_bill_analyzer setup
  ```
- For Ollama: Make sure Ollama is running (`ollama serve`)

#### "No bills found"
- Make sure you've added bills first with the `add` command

### Phase 2 Issues

#### "No data found" when running stats
- You need to have added bills first with the `add` command
- If you're using `--year` filter, make sure you have bills for that year
- Try running without filters first: `python -m medical_bill_analyzer stats --by practitioner`

#### Stats show "Unknown" for practitioner or category
- This happens when the LLM extraction didn't identify the practitioner name or type
- The bill is still counted in statistics, just categorized as "Unknown"
- You can review bills with `list` command and check extraction status

#### Monthly stats are missing some months
- Only months with bills are shown
- If you don't have bills for a month, it won't appear in the output
- Use `--year 2024` to see all months with data for that year

#### Percentages in category stats don't seem right
- Percentages are calculated based on all bills in the filtered set
- If you're using `--year` filter, percentages are relative to that year only
- Try without filters to see overall percentages

---

## Database and Config Locations

- **Config**: `~/.medical-bill-analyzer/config.yaml`
- **Database** (including API keys): `~/.medical-bill-analyzer/data/medical_bills.db`
- **PDF Storage**: `~/.medical-bill-analyzer/data/pdfs/`
- **Logs**: `~/.medical-bill-analyzer/logs/`

**Note**: API keys are stored securely in the database, not in environment variables or separate files.

To reset everything, simply delete the `.medical-bill-analyzer` directory:
```bash
rm -rf ~/.medical-bill-analyzer
```

---

## What to Test With Real Data

1. **A real German medical bill PDF**:
   - Should extract practitioner name
   - Should extract date (German format DD.MM.YYYY)
   - Should extract total amount (in EUR)
   - Should identify practitioner type (Arzt, Zahnarzt, etc.)

2. **Multiple bills from different practitioners**:
   - Should calculate correct totals
   - Should show all in list command
   - Should group correctly by type

3. **Bills from different years**:
   - Should filter correctly by year
   - Should give correct bonus recommendation per year

---

## Success Criteria

### Phase 1 - Core Functionality
✅ The application is working correctly if:
1. Setup completes without errors
2. Bills are extracted and stored
3. List shows your bills correctly
4. Total matches your expectations
5. Bonus recommendation makes sense given your costs

🎉 **If all Phase 1 tests pass, MVP is complete!**

### Phase 2 - Enhanced Analytics
✅ Analytics are working correctly if:
1. Practitioner stats show all doctors sorted by spending
2. `--top N` correctly limits the number of results
3. Category breakdown shows percentages that add up to 100%
4. Visual percentage bars appear for categories
5. Monthly stats are in chronological order
6. Year and type filters work as expected
7. Summary totals match the `total` command output

🎉 **If all Phase 2 tests pass, Enhanced Analytics is complete!**
