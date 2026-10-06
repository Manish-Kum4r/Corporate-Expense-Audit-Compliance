-- ============================================================
-- Corporate Expense Audit - SQL Queries
-- Author: Manish Kumar
-- Date: Oct 2025
-- Purpose: Expense audit queries for Concur-style data
-- ============================================================

-- -------------------------------------------------------
-- 1. Policy Violation Detection: Amount exceeds limit
-- -------------------------------------------------------
SELECT 
    e.Employee_ID,
    e.Employee_Name,
    e.Department,
    e.Expense_Type,
    e.Amount_INR,
    e.Country,
    CASE 
        WHEN e.Country != 'India' AND e.Amount_INR > 175000 AND e.Expense_Type = 'Flight' THEN 'Exceeds International Flight Limit'
        WHEN e.Country != 'India' AND e.Amount_INR > 30000 AND e.Expense_Type = 'Hotel' THEN 'Exceeds International Hotel Limit'
        WHEN e.Country != 'India' AND e.Amount_INR > 50000 AND e.Expense_Type = 'Client Entertainment' THEN 'Exceeds Int. Entertainment Limit'
        WHEN e.Country = 'India' AND e.Amount_INR > 25000 AND e.Expense_Type = 'Flight' THEN 'Exceeds Domestic Flight Limit'
        WHEN e.Country = 'India' AND e.Amount_INR > 12000 AND e.Expense_Type = 'Hotel' THEN 'Exceeds Domestic Hotel Limit'
        WHEN e.Country = 'India' AND e.Amount_INR > 25000 AND e.Expense_Type = 'Client Entertainment' THEN 'Exceeds Domestic Entertainment Limit'
        WHEN e.Amount_INR > 2000 AND e.Expense_Type = 'Meals' AND e.Country = 'India' THEN 'Exceeds Domestic Meal Limit'
        WHEN e.Amount_INR > 8000 AND e.Expense_Type = 'Meals' AND e.Country != 'India' THEN 'Exceeds Int. Meal Limit'
        ELSE 'Other Violation'
    END AS Violation_Type,
    CASE 
        WHEN e.Amount_INR > 100000 THEN 'CRITICAL'
        WHEN e.Amount_INR > 50000 THEN 'HIGH'
        WHEN e.Amount_INR > 25000 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS Severity
FROM expense_data e
WHERE 
    (e.Country != 'India' AND e.Expense_Type = 'Flight' AND e.Amount_INR > 175000)
    OR (e.Country != 'India' AND e.Expense_Type = 'Hotel' AND e.Amount_INR > 30000)
    OR (e.Country != 'India' AND e.Expense_Type = 'Client Entertainment' AND e.Amount_INR > 50000)
    OR (e.Country = 'India' AND e.Expense_Type = 'Flight' AND e.Amount_INR > 25000)
    OR (e.Country = 'India' AND e.Expense_Type = 'Hotel' AND e.Amount_INR > 12000)
    OR (e.Country = 'India' AND e.Expense_Type = 'Client Entertainment' AND e.Amount_INR > 25000)
    OR (e.Expense_Type = 'Meals' AND ((e.Country = 'India' AND e.Amount_INR > 2000) OR (e.Country != 'India' AND e.Amount_INR > 8000)))
ORDER BY Amount_INR DESC;


-- -------------------------------------------------------
-- 2. Missing Receipt Detection
-- -------------------------------------------------------
SELECT 
    Employee_ID,
    Employee_Name,
    Department,
    Expense_Type,
    Amount_INR,
    Expense_Date,
    'MISSING RECEIPT' AS Violation_Type,
    'MEDIUM' AS Severity
FROM expense_data
WHERE Receipt_Available = 'No' 
  AND Amount_INR > 500
ORDER BY Amount_INR DESC;


-- -------------------------------------------------------
-- 3. Pre-Approval Missing for Entertainment/International
-- -------------------------------------------------------
SELECT 
    Employee_ID,
    Employee_Name,
    Department,
    Expense_Type,
    Amount_INR,
    Country,
    'NO PRE-APPROVAL' AS Violation_Type,
    CASE 
        WHEN Expense_Type = 'Client Entertainment' THEN 'HIGH'
        WHEN Country != 'India' THEN 'HIGH'
        ELSE 'MEDIUM'
    END AS Severity
FROM expense_data
WHERE Pre_Approval = 'No'
  AND (
      Expense_Type = 'Client Entertainment'
      OR (Country != 'India' AND Expense_Type IN ('Flight', 'Hotel'))
  )
ORDER BY Amount_INR DESC;


-- -------------------------------------------------------
-- 4. Weekend Expense Without Travel Plan
-- -------------------------------------------------------
SELECT 
    Employee_ID,
    Employee_Name,
    Department,
    Expense_Type,
    Amount_INR,
    Expense_Date,
    DAYNAME(Expense_Date) AS Day_of_Week,
    'WEEKEND EXPENSE - NO APPROVED PLAN' AS Violation_Type,
    'MEDIUM' AS Severity
FROM expense_data
WHERE DAYOFWEEK(Expense_Date) IN (1, 7)  -- Sunday, Saturday
  AND Weekend_Travel = 'No'
  AND Pre_Approval = 'No'
ORDER BY Expense_Date DESC;


-- -------------------------------------------------------
-- 5. Late Filing Detection (>30 days after expense date)
-- -------------------------------------------------------
SELECT 
    Employee_ID,
    Employee_Name,
    Department,
    Expense_Date,
    Submission_Date,
    DATEDIFF(Submission_Date, Expense_Date) AS Days_Delay,
    Amount_INR,
    'LATE FILING' AS Violation_Type,
    'LOW' AS Severity
FROM expense_data
WHERE DATEDIFF(Submission_Date, Expense_Date) > 30
ORDER BY Days_Delay DESC;


-- -------------------------------------------------------
-- 6. Duplicate Claim Detection
-- -------------------------------------------------------
SELECT 
    e1.Employee_ID,
    e1.Employee_Name,
    e1.Department,
    e1.Expense_Type,
    e1.Amount_INR,
    e1.Expense_Date,
    e1.Submission_Date AS Submit_1,
    e2.Submission_Date AS Submit_2,
    'DUPLICATE CLAIM' AS Violation_Type,
    'CRITICAL' AS Severity
FROM expense_data e1
JOIN expense_data e2 
    ON e1.Employee_ID = e2.Employee_ID
    AND e1.Expense_Date = e2.Expense_Date
    AND e1.Expense_Type = e2.Expense_Type
    AND e1.Amount_INR = e2.Amount_INR
    AND e1.Submission_Date != e2.Submission_Date
ORDER BY e1.Employee_ID, e1.Expense_Date;


-- -------------------------------------------------------
-- 7. Department-wise Compliance Summary
-- -------------------------------------------------------
SELECT 
    Department,
    COUNT(*) AS Total_Claims,
    SUM(Amount_INR) AS Total_Amount,
    SUM(CASE WHEN 
        (Country != 'India' AND Expense_Type = 'Flight' AND Amount_INR > 175000)
        OR (Country != 'India' AND Expense_Type = 'Hotel' AND Amount_INR > 30000)
        OR Receipt_Available = 'No' AND Amount_INR > 500
        OR (Pre_Approval = 'No' AND Expense_Type = 'Client Entertainment')
        THEN 1 ELSE 0 
    END) AS Violations,
    ROUND(
        (1.0 - SUM(CASE WHEN 
            (Country != 'India' AND Expense_Type = 'Flight' AND Amount_INR > 175000)
            OR (Country != 'India' AND Expense_Type = 'Hotel' AND Amount_INR > 30000)
            OR Receipt_Available = 'No' AND Amount_INR > 500
            OR (Pre_Approval = 'No' AND Expense_Type = 'Client Entertainment')
            THEN 1 ELSE 0 
        END) / COUNT(*)) * 100, 1
    ) AS Compliance_Score_Pct
FROM expense_data
GROUP BY Department
ORDER BY Compliance_Score_Pct ASC;


-- -------------------------------------------------------
-- 8. Employee Risk Score (repeat violators)
-- -------------------------------------------------------
SELECT 
    Employee_ID,
    Employee_Name,
    Department,
    COUNT(*) AS Violation_Count,
    SUM(Amount_INR) AS Total_Flagged_Amount,
    CASE 
        WHEN COUNT(*) >= 5 THEN 'CRITICAL RISK'
        WHEN COUNT(*) >= 3 THEN 'HIGH RISK'
        WHEN COUNT(*) >= 2 THEN 'MEDIUM RISK'
        ELSE 'LOW RISK'
    END AS Risk_Level
FROM (
    SELECT Employee_ID, Employee_Name, Department, Expense_Type, Amount_INR
    FROM expense_data
    WHERE 
        (Country != 'India' AND ((Expense_Type = 'Flight' AND Amount_INR > 175000) OR (Expense_Type = 'Hotel' AND Amount_INR > 30000)))
        OR Receipt_Available = 'No' AND Amount_INR > 500
        OR (Pre_Approval = 'No' AND Expense_Type = 'Client Entertainment')
        OR (DAYOFWEEK(Expense_Date) IN (1, 7) AND Weekend_Travel = 'No')
) violations
GROUP BY Employee_ID, Employee_Name, Department
HAVING COUNT(*) >= 1
ORDER BY Violation_Count DESC;


-- -------------------------------------------------------
-- 9. Monthly Trend - Claims vs Violations
-- -------------------------------------------------------
SELECT 
    DATE_FORMAT(Expense_Date, '%Y-%m') AS Month,
    COUNT(*) AS Total_Claims,
    SUM(Amount_INR) AS Total_Amount,
    SUM(CASE WHEN 
        (Country != 'India' AND Expense_Type = 'Flight' AND Amount_INR > 175000)
        OR Receipt_Available = 'No' AND Amount_INR > 500
        OR (Pre_Approval = 'No' AND Expense_Type = 'Client Entertainment')
        THEN 1 ELSE 0 
    END) AS Violations
FROM expense_data
GROUP BY DATE_FORMAT(Expense_Date, '%Y-%m')
ORDER BY Month;


-- -------------------------------------------------------
-- 10. Escalation Priority Queue
-- -------------------------------------------------------
SELECT 
    CASE 
        WHEN Severity = 'CRITICAL' THEN 1
        WHEN Severity = 'HIGH' THEN 2
        WHEN Severity = 'MEDIUM' THEN 3
        ELSE 4
    END AS Priority,
    Employee_ID,
    Employee_Name,
    Department,
    Violation_Type,
    Amount_INR,
    Severity,
    CASE 
        WHEN Severity = 'CRITICAL' THEN 'Notify VP + Finance Director → CFO/Compliance'
        WHEN Severity = 'HIGH' THEN 'VP Approval Required'
        WHEN Severity = 'MEDIUM' THEN 'Manager Review within 48 hours'
        ELSE 'Auto-approve with flag'
    END AS Escalation_Path
FROM (
    -- Combined violations from all checks above (union all)
    SELECT Employee_ID, Employee_Name, Department, Expense_Type AS Violation_Type, Amount_INR,
           CASE WHEN Amount_INR > 100000 THEN 'CRITICAL' WHEN Amount_INR > 50000 THEN 'HIGH' ELSE 'MEDIUM' END AS Severity
    FROM expense_data
    WHERE (Country != 'India' AND Expense_Type = 'Flight' AND Amount_INR > 175000)
       OR (Country != 'India' AND Expense_Type = 'Client Entertainment' AND Amount_INR > 50000)
) combined_violations
ORDER BY Priority, Amount_INR DESC;
