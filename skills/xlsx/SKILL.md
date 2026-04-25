---
name: xlsx
description: "Spreadsheet creation, editing, and analysis. Two approaches: Programmatic (openpyxl/pandas for .xlsx files with formulas, formatting, and data analysis) and Browser-based (Excel Online via Playwright for pivot tables, charts, and collaboration). Use when the user wants to create, read, edit, or fix .xlsx/.xlsm/.csv/.tsv files, or work with Excel Online."
---

# XLSX — Spreadsheet Skill

Two approaches for working with spreadsheets depending on the task:

| Approach | Tool | Best For |
|----------|------|----------|
| Programmatic | openpyxl / pandas | Creating files, bulk data, formulas, automation |
| Browser-based | Excel Online via Playwright | Pivot tables, charts, collaboration, interactive editing |

---

## Part 1: Programmatic Approach (openpyxl / pandas)

### Requirements for All Excel Outputs

#### Professional Font
- Use a consistent, professional font (e.g., Arial, Times New Roman) unless otherwise instructed

#### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

#### Preserve Existing Templates
- Study and EXACTLY match existing format, style, and conventions when modifying files
- Existing template conventions ALWAYS override these guidelines

### Financial Model Standards

#### Color Coding (Industry-Standard)
- **Blue text (RGB: 0,0,255)**: Hardcoded inputs and scenario-adjustable numbers
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations
- **Green text (RGB: 0,128,0)**: Links pulling from other worksheets
- **Red text (RGB: 255,0,0)**: External links to other files
- **Yellow background (RGB: 255,255,0)**: Key assumptions needing attention

#### Number Formatting
- **Years**: Format as text strings ("2024" not "2,024")
- **Currency**: Use $#,##0 format; ALWAYS specify units in headers ("Revenue ($mm)")
- **Zeros**: Use formatting to display as "-" including percentages
- **Percentages**: Default to 0.0% format (one decimal)
- **Multiples**: Format as 0.0x for valuation multiples
- **Negative numbers**: Use parentheses (123) not minus -123

#### Formula Rules
- Place ALL assumptions in separate cells, use cell references in formulas
- Use `=B5*(1+$B$6)` instead of `=B5*1.05`
- Document hardcodes with source comments

### CRITICAL: Use Formulas, Not Hardcoded Values

Always use Excel formulas instead of calculating values in Python and hardcoding them.

```python
# WRONG - Hardcoding calculated values
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000

# CORRECT - Using Excel formulas
sheet['B10'] = '=SUM(B2:B9)'
sheet['C5'] = '=(C4-C2)/C2'
sheet['D20'] = '=AVERAGE(D2:D19)'
```

### Reading and Analyzing Data

```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx')                    # Default: first sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # All sheets as dict

# Analyze
df.head()      # Preview data
df.info()      # Column info
df.describe()  # Statistics

# Write Excel
df.to_excel('output.xlsx', index=False)
```

### Creating New Excel Files

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# Add data
sheet['A1'] = 'Hello'
sheet['B1'] = 'World'
sheet.append(['Row', 'of', 'data'])

# Add formula
sheet['B2'] = '=SUM(A1:A10)'

# Formatting
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# Column width
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### Editing Existing Files

```python
from openpyxl import load_workbook

wb = load_workbook('existing.xlsx')
sheet = wb.active  # or wb['SheetName']

# Working with multiple sheets
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]

# Modify cells
sheet['A1'] = 'New Value'
sheet.insert_rows(2)
sheet.delete_cols(3)

# Add new sheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

### Recalculating Formulas

**LibreOffice Required**: Use the provided `scripts/recalc.py` script to recalculate formula values.

```bash
python scripts/recalc.py output.xlsx 30
```

The script:
- Automatically sets up LibreOffice macro on first run
- Recalculates all formulas in all sheets
- Scans ALL cells for Excel errors
- Returns JSON with detailed error locations and counts

```json
{
  "status": "success",
  "total_errors": 0,
  "total_formulas": 42,
  "error_summary": {}
}
```

### Formula Verification Checklist

- [ ] Test 2-3 sample references before building full model
- [ ] Confirm column mapping (column 64 = BL, not BK)
- [ ] Remember row offset (DataFrame row 5 = Excel row 6)
- [ ] Handle NaN with `pd.notna()`
- [ ] Check far-right columns (FY data often in columns 50+)
- [ ] Verify cross-sheet references use correct format (Sheet1!A1)
- [ ] Test edge cases: zero, negative, and very large values

### Library Selection Guide

- **pandas**: Best for data analysis, bulk operations, simple data export
- **openpyxl**: Best for complex formatting, formulas, and Excel-specific features
- **Warning**: `load_workbook('file.xlsx', data_only=True)` replaces formulas with values if saved

---

## Part 2: Browser-Based Approach (Excel Online)

For interactive spreadsheet work via Playwright MCP automation.

### Setup

Configure via canifi-env:
```bash
canifi-env set MICROSOFT_EMAIL "your-email@outlook.com"
```

### Authentication Options

**Option 1: Manual Browser Login (Recommended)**
1. Complete Browser Automation Setup using CDP mode
2. Login to Excel Online manually in the Playwright-controlled Chrome window
3. Claude uses your authenticated session without seeing your password

**Option 2: Environment Variables**
```bash
canifi-env set SERVICE_EMAIL "your-email"
canifi-env set SERVICE_PASSWORD "your-password"
```

### Browser Capabilities
- Create and edit spreadsheets
- Build formulas and functions
- Create charts and visualizations
- Apply conditional formatting
- Create pivot tables
- Sort and filter data
- Use data validation
- Import and export data
- Collaborate in real-time

### Usage Examples

**Create Spreadsheet:**
```
User: "Create an expense tracker in Excel"
Claude: Creates new workbook "Expense Tracker", adds columns for
        Date, Category, Description, Amount. Adds SUM formula for total.
```

**Analyze Data:**
```
User: "Create a pivot table from my sales data"
Claude: Selects data range, inserts pivot table,
        configures rows, columns, and values.
```

**Create Chart:**
```
User: "Make a line chart showing revenue trends"
Claude: Selects revenue data, inserts line chart,
        adds titles and labels.
```

### Selectors Reference

```javascript
// New workbook
'[aria-label="New blank workbook"]'

// Cell input
'.formulabar-input' or 'input[name="Cell"]'

// Ribbon tabs
'[role="tablist"]'
'[aria-label="Insert"]'
'[aria-label="Formulas"]'
'[aria-label="Data"]'

// Actions
'[aria-label="Insert chart"]'
'[aria-label="Sort"]'
'[aria-label="Filter"]'
```

### Common Formulas

```
=SUM(A1:A10)              // Sum range
=AVERAGE(A1:A10)          // Average
=VLOOKUP(key,range,col,0) // Vertical lookup
=IF(condition,true,false)  // Conditional
=COUNTIF(range,criteria)   // Count matching
=SUMIF(range,crit,sum)     // Sum matching
=TEXT(A1,"format")         // Format text
=TODAY()                   // Current date
=CONCATENATE(A1,B1)        // Join text
```

### Error Handling
- **Login Failed**: Retry 3 times, notify user
- **Session Expired**: Re-authenticate automatically
- **Workbook Not Found**: Search OneDrive, ask for clarification
- **Formula Error**: Identify error type, suggest fix
- **Save Failed**: Enable AutoSave, retry

### Excel Online Limitations
- Auto-saves to OneDrive
- Some advanced features only in desktop version
- Maximum rows: 1,048,576 per sheet
- Power Query limited in online version
- Macros not supported in online version
- Can open and edit .xlsx, .xlsm files

---

## Code Style Guidelines

**For Python code**: Write minimal, concise code without unnecessary comments or verbose variable names.

**For Excel files**: Add comments to cells with complex formulas, document data sources for hardcoded values, include notes for key calculations.
