-- Example queries after importing data/patient_visits.csv as patient_visits.
SELECT strftime('%Y-%m', visit_date) AS month, COUNT(*) AS visits,
       ROUND(AVG(wait_minutes), 1) AS avg_wait_minutes,
       ROUND(AVG(length_of_stay_days), 2) AS avg_stay_days
FROM patient_visits
GROUP BY month ORDER BY month;

SELECT department, COUNT(*) AS visits, ROUND(AVG(wait_minutes), 1) AS avg_wait_minutes
FROM patient_visits GROUP BY department ORDER BY visits DESC;
