from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(ROOT/"data/patient_visits.csv",parse_dates=["visit_date"]).drop_duplicates()
df["month"]=df.visit_date.dt.to_period("M").astype(str)
monthly=df.groupby("month",as_index=False).agg(visits=("visit_id","count"),avg_wait_minutes=("wait_minutes","mean"),avg_stay_days=("length_of_stay_days","mean")).round(2)
department=df.groupby("department",as_index=False).agg(visits=("visit_id","count"),avg_wait_minutes=("wait_minutes","mean"),avg_stay_days=("length_of_stay_days","mean")).round(2).sort_values("visits",ascending=False)
out=ROOT/"outputs"; out.mkdir(exist_ok=True); monthly.to_csv(out/"monthly_summary.csv",index=False); department.to_csv(out/"department_summary.csv",index=False)
ax=monthly.plot(x="month",y="visits",kind="line",marker="o",legend=False,figsize=(9,4),title="Monthly visits (sample data)"); ax.set_ylabel("Visits"); ax.grid(alpha=.25); plt.tight_layout(); plt.savefig(out/"monthly_visits.png",dpi=150); plt.close()
print(f"Summarized {len(df)} sample visits. Files saved to {out}")
