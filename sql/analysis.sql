-- Example queries for outputs/england_monthly_ae.csv.
-- This is England-wide monthly aggregate data, not individual provider records.

-- Recent monthly activity and performance.
SELECT
    Period,
    Attendances,
    EmergencyAdmissions,
    Within4HoursPct,
    WaitOver12HoursAfterDecision
FROM england_monthly_ae
WHERE Period >= DATE '2024-01-01'
ORDER BY Period;

-- Average four-hour performance by calendar month across available years.
SELECT
    Month,
    AVG(Within4HoursPct) AS avg_within_four_hours_pct
FROM england_monthly_ae
WHERE Period >= DATE '2015-06-01'
GROUP BY Month
ORDER BY MIN(EXTRACT(MONTH FROM Period));
