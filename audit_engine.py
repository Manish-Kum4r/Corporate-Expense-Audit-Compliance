"""
Corporate Expense Audit Engine
==============================
Processes T&E expense claims against firm-wide expense policies.
Generates violation reports, escalation lists, and compliance metrics.

Author: Manish Kumar
Date: Oct 2025
Version: 1.2
"""

import csv
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple

# ---------- Config ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

POLICY_FILE = os.path.join(DATA_DIR, "expense_policies.csv")
EXPENSE_FILE = os.path.join(DATA_DIR, "sample_expense_data.csv")
ESCALATION_FILE = os.path.join(DATA_DIR, "escalation_matrix.csv")

# Policy limits (INR) - hardcoded for quick overrides
POLICY_LIMITS = {
    "AIR_DOM": 25000,
    "AIR_INT": 175000,   # up to 8hr flights
    "HTL_DOM": 12000,    # per night
    "HTL_INT": 30000,    # per night (Tier 1)
    "HTL_INT_PREMIUM": 50000,  # approved premium hotels only
    "MEAL_DOM": 2000,
    "MEAL_INT": 8000,
    "TRANS_DOM": 3000,   # per day
    "TRANS_INT": 15000,  # per day
    "ENT_DOM": 25000,    # pre-approval mandatory
    "ENT_INT": 50000,    # pre-approval mandatory + VP approval
}

# Severity levels
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"


def load_expenses(filepath: str) -> List[Dict]:
    """Load expense records from CSV file."""
    expenses = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["Amount_INR"] = float(row["Amount_INR"])
            # Parse dates
            row["Submission_Date"] = datetime.strptime(row["Submission_Date"], "%Y-%m-%d")
            row["Expense_Date"] = datetime.strptime(row["Expense_Date"], "%Y-%m-%d")
            # Boolean fields
            row["Receipt_Available"] = row["Receipt_Available"].strip() == "Yes"
            row["Pre_Approval"] = row["Pre_Approval"].strip() == "Yes"
            row["Weekend_Travel"] = row["Weekend_Travel"].strip() == "Yes"
            expenses.append(row)
    return expenses


def load_policies(filepath: str) -> List[Dict]:
    """Load policy rules from CSV."""
    policies = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["Max_Limit_INR"] = float(row["Max_Limit_INR"])
            policies.append(row)
    return policies


def is_weekend(expense_date: datetime) -> bool:
    """Check if expense date falls on weekend (Sat=5, Sun=6)."""
    return expense_date.weekday() in [5, 6]


def calculate_delay_days(submission_date: datetime, expense_date: datetime) -> int:
    """Calculate days between expense date and submission date."""
    return (submission_date - expense_date).days


def audit_single_expense(expense: Dict, policies: List[Dict]) -> List[Dict]:
    """
    Audit a single expense claim against all applicable policies.
    Returns list of violations found.
    """
    violations = []
    exp_type = expense["Expense_Type"]
    category = expense["Category_Code"]
    amount = expense["Amount_INR"]
    is_intl = expense["Country"].strip() != "India"
    travel_type = "International" if is_intl else "Domestic"

    # ---- Rule 1: Amount limit check ----
    limit_key = category  # e.g., AIR_DOM, HTL_INT
    if limit_key in POLICY_LIMITS:
        limit = POLICY_LIMITS[limit_key]
        if amount > limit:
            severity = SEVERITY_CRITICAL if limit_key in ["HTL_INT_PREMIUM", "ENT_INT"] else SEVERITY_HIGH
            if amount > limit * 2:
                severity = SEVERITY_CRITICAL
            violations.append({
                "claim_id": f"CLM-2025-{expense['Employee_ID'][-3:]}-{exp_type[:3].upper()}",
                "employee": f"{expense['Employee_ID']} - {expense['Employee_Name']}",
                "department": expense["Department"],
                "expense_type": exp_type,
                "amount": amount,
                "violation": f"Amount ₹{amount:,.0f} exceeds {travel_type} {exp_type} limit of ₹{limit:,.0f}",
                "severity": severity,
                "policy_ref": f"POL for {limit_key}"
            })

    # ---- Rule 2: Receipt mandatory for > ₹500 ----
    if amount > 500 and not expense["Receipt_Available"]:
        violations.append({
            "claim_id": f"CLM-2025-{expense['Employee_ID'][-3:]}-{exp_type[:3].upper()}",
            "employee": f"{expense['Employee_ID']} - {expense['Employee_Name']}",
            "department": expense["Department"],
            "expense_type": exp_type,
            "amount": amount,
            "violation": "Missing receipt for amount > ₹500",
            "severity": SEVERITY_MEDIUM,
            "policy_ref": "POL013"
        })

    # ---- Rule 3: Pre-approval check for entertainment + international ----
    if exp_type == "Client Entertainment" and not expense["Pre_Approval"]:
        violations.append({
            "claim_id": f"CLM-2025-{expense['Employee_ID'][-3:]}-{exp_type[:3].upper()}",
            "employee": f"{expense['Employee_ID']} - {expense['Employee_Name']}",
            "department": expense["Department"],
            "expense_type": exp_type,
            "amount": amount,
            "violation": "No pre-approval for Client Entertainment expense",
            "severity": SEVERITY_HIGH if is_intl else SEVERITY_HIGH,
            "policy_ref": "POL011/POL012"
        })

    if is_intl and exp_type in ["Flight", "Hotel"] and not expense["Pre_Approval"]:
        violations.append({
            "claim_id": f"CLM-2025-{expense['Employee_ID'][-3:]}-{exp_type[:3].upper()}",
            "employee": f"{expense['Employee_ID']} - {expense['Employee_Name']}",
            "department": expense["Department"],
            "expense_type": exp_type,
            "amount": amount,
            "violation": f"No pre-approval for international {exp_type}",
            "severity": SEVERITY_HIGH,
            "policy_ref": "POL014"
        })

    # ---- Rule 4: Weekend expense check ----
    if is_weekend(expense["Expense_Date"]) and not expense["Weekend_Travel"] and not expense["Pre_Approval"]:
        violations.append({
            "claim_id": f"CLM-2025-{expense['Employee_ID'][-3:]}-{exp_type[:3].upper()}",
            "employee": f"{expense['Employee_ID']} - {expense['Employee_Name']}",
            "department": expense["Department"],
            "expense_type": exp_type,
            "amount": amount,
            "violation": "Weekend expense without approved travel plan",
            "severity": SEVERITY_MEDIUM,
            "policy_ref": "POL015"
        })

    # ---- Rule 5: Late filing (>30 days) ----
    delay = calculate_delay_days(expense["Submission_Date"], expense["Expense_Date"])
    if delay > 30:
        violations.append({
            "claim_id": f"CLM-2025-{expense['Employee_ID'][-3:]}-{exp_type[:3].upper()}",
            "employee": f"{expense['Employee_ID']} - {expense['Employee_Name']}",
            "department": expense["Department"],
            "expense_type": exp_type,
            "amount": amount,
            "violation": f"Late filing - {delay} days after expense date (>30 day policy)",
            "severity": SEVERITY_LOW,
            "policy_ref": "POL017"
        })

    return violations


def detect_duplicates(expenses: List[Dict]) -> List[Dict]:
    """
    Detect duplicate claims - same employee, same date, same amount.
    TODO: extend to fuzzy matching (within 5% amount tolerance)
    """
    seen = {}
    duplicates = []

    for exp in expenses:
        key = (exp["Employee_ID"], exp["Expense_Date"].strftime("%Y-%m-%d"), exp["Expense_Type"], exp["Amount_INR"])
        if key in seen:
            duplicates.append({
                "claim_id": f"CLM-2025-{exp['Employee_ID'][-3:]}-{exp['Expense_Type'][:3].upper()}-DUP",
                "employee": f"{exp['Employee_ID']} - {exp['Employee_Name']}",
                "department": exp["Department"],
                "expense_type": exp["Expense_Type"],
                "amount": exp["Amount_INR"],
                "violation": f"DUPLICATE CLAIM - matches claim from {seen[key]['Submission_Date'].strftime('%Y-%m-%d')}",
                "severity": SEVERITY_CRITICAL,
                "policy_ref": "POL016"
            })
        else:
            seen[key] = exp

    return duplicates


def run_full_audit() -> Dict:
    """
    Main audit function - runs all checks and generates report.
    """
    print("=" * 60)
    print("CORPORATE EXPENSE AUDIT ENGINE v1.2")
    print("=" * 60)

    # Load data
    expenses = load_expenses(EXPENSE_FILE)
    policies = load_policies(POLICY_FILE)
    print(f"\nLoaded {len(expenses)} expense records")
    print(f"Loaded {len(policies)} policy rules")

    # Run per-claim audit
    all_violations = []
    for exp in expenses:
        violations = audit_single_expense(exp, policies)
        all_violations.extend(violations)

    # Run duplicate detection
    duplicates = detect_duplicates(expenses)
    all_violations.extend(duplicates)

    # Aggregate metrics
    total_claims = len(expenses)
    total_violations = len(all_violations)
    unique_violators = set(v["employee"] for v in all_violations)
    total_amount = sum(e["Amount_INR"] for e in expenses)
    flagged_amount = sum(v["amount"] for v in all_violations)

    # Department-wise breakdown
    dept_stats = defaultdict(lambda: {"claims": 0, "violations": 0, "amount": 0})
    for exp in expenses:
        dept_stats[exp["Department"]]["claims"] += 1
        dept_stats[exp["Department"]]["amount"] += exp["Amount_INR"]
    for v in all_violations:
        dept_stats[v["department"]]["violations"] += 1

    # Severity breakdown
    severity_counts = defaultdict(int)
    for v in all_violations:
        severity_counts[v["severity"]] += 1

    # Compliance score
    compliant_claims = total_claims - len(unique_violators)
    compliance_score = (compliant_claims / total_claims) * 100 if total_claims > 0 else 0

    report = {
        "summary": {
            "total_claims": total_claims,
            "total_violations": total_violations,
            "unique_violators": len(unique_violators),
            "total_amount_inr": total_amount,
            "flagged_amount_inr": flagged_amount,
            "compliance_score_pct": round(compliance_score, 1),
            "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        "violations": all_violations,
        "department_stats": dict(dept_stats),
        "severity_breakdown": dict(severity_counts)
    }

    # Save report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, "audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport saved to: {report_path}")

    # Print summary
    print(f"\n{'=' * 40}")
    print(f"AUDIT SUMMARY")
    print(f"{'=' * 40}")
    print(f"Total Claims Reviewed:  {total_claims}")
    print(f"Violations Found:       {total_violations}")
    print(f"Unique Violators:       {len(unique_violators)}")
    print(f"Total Amount:           ₹{total_amount:,.0f}")
    print(f"Flagged Amount:         ₹{flagged_amount:,.0f}")
    print(f"Compliance Score:       {compliance_score:.1f}%")
    print(f"\nSeverity Breakdown:")
    for sev, count in sorted(severity_counts.items()):
        print(f"  {sev:10s}: {count}")

    print(f"\nTop Violators:")
    violator_counts = defaultdict(int)
    for v in all_violations:
        violator_counts[v["employee"]] += 1
    for emp, count in sorted(violator_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {emp}: {count} violations")

    return report


if __name__ == "__main__":
    report = run_full_audit()
