# Hospital Patient Analytics Dashboard

A basic operations dashboard dataset and analysis script for practicing visit-volume, wait-time, length-of-stay, and disposition summaries. Every row is generated sample data. There are no names, addresses, medical record numbers, or actual patient records. This is not clinical advice.

Run: `python hospital-patient-dashboard/src/analyze_visits.py`

The script writes monthly summaries, department summaries, and a chart in `outputs/`. Import `data/patient_visits.csv` into Power BI and use the field guide below to build a simple dashboard.

## Suggested Power BI visuals

- Cards: visit count, average wait (minutes), average stay (days).
- Line chart: visits by month.
- Bar chart: visits by department.
- Slicers: department, visit type, and disposition.

## Field guide

`visit_id` is a synthetic row identifier; `visit_date` is the visit date; `department` and `visit_type` describe the visit; `wait_minutes` and `length_of_stay_days` are numeric measures; `disposition` is the recorded outcome category.
