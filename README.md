# Corporate Expense Audit & Compliance System

A portfolio project built around a realistic **corporate Travel & Entertainment (T&E) expense review** process. It is designed to show the skills used in an Expense Management / Business Support Management role: policy checking, exception analysis, escalation prioritisation, reporting and basic statistical review.

## Skills demonstrated

- **SQL:** reusable queries for policy breaches, missing receipts, late submissions, duplicates, department compliance and escalation queues.
- **Python:** audit engine, rule-based exception detection, duplicate checks, summary metrics and PNG dashboard generation.
- **Power BI:** one-page dark-theme dashboard layout and KPI design; the source CSVs can be loaded into Power BI for an interactive version.
- **Excel:** review workbook with source data, formulas, filters and statistical-review notes.
- **Statistics:** compliance rate, severity distribution, department comparison, Pareto thinking, median/mean comparison and outlier review.

## Deliverables

```
Corporate-Expense-Audit-System/
├── output/expense_audit_dashboard.png  # single-page Power BI-style dashboard
├── output/audit_report.json             # Python audit output
├── output/expense_audit_review.xlsx    # Excel review workbook
├── scripts/audit_engine.py              # Python audit engine
├── generate_dashboard.py                # Python PNG dashboard generator
├── create_excel_workbook.py             # Excel workbook generator
├── sql/audit_queries.sql                # audit queries
├── data/sample_expense_data.csv         # synthetic T&E claims
├── data/expense_policies.csv            # policy thresholds
└── data/escalation_matrix.csv           # severity-to-action workflow
```

## How to run

From the project folder:

```bash
python scripts/audit_engine.py
python generate_dashboard.py
python create_excel_workbook.py
```

The project uses Python standard-library code for the audit engine. `matplotlib`, `seaborn` and `openpyxl` are used only to generate the PNG and Excel outputs.

## Current audit snapshot

The synthetic review population contains **91 claims**. The Python engine identified **57 rule exceptions** across **16 employees**, with a calculated compliance score of **82.4%**. These are sample values for demonstration, not real company data.

## Business workflow

1. Load expense claims and policy thresholds.
2. Check amount limits, receipts, approvals, weekend activity, late filing and duplicate claims.
3. Assign LOW / MEDIUM / HIGH / CRITICAL severity.
4. Prioritise exceptions for manager, VP, Finance or Compliance review.
5. Review department and employee trends in the one-page dashboard.
6. Use the Excel sheet for manual evidence review and the SQL queries for repeatable controls.

## Interview explanation

> I built a rule-based T&E expense audit process using SQL and Python. It reviews claims against policy limits, receipt and approval requirements, late filing and duplicate patterns. I then summarised exceptions by department and severity in a Power BI-style one-page dashboard, while keeping an Excel review workbook for operational follow-up. The statistical part focuses on compliance rate, exception concentration and outlier prioritisation.

All data is synthetic and created for portfolio use.
