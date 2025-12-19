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

## Testing Checklist

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

---

## Troubleshooting

### "Configuration error"
- Run `python -m medical_bill_analyzer setup` first

### "API key not found" or "Connection failed"
- The setup wizard should have prompted you to enter your API key
- Your API key is saved securely in the database (`~/.medical-bill-analyzer/data/medical_bills.db`)
- If you need to update it, run the setup wizard again:
  ```bash
  python -m medical_bill_analyzer setup
  ```
- For Ollama: Make sure Ollama is running (`ollama serve`)

### "No bills found"
- Make sure you've added bills first with the `add` command

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

✅ The application is working correctly if:
1. Setup completes without errors
2. Bills are extracted and stored
3. List shows your bills correctly
4. Total matches your expectations
5. Bonus recommendation makes sense given your costs

🎉 **If all tests pass, Phase 1 MVP is complete!**
