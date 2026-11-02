from pathlib import Path
import json
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nhs_monthly_ae_timeseries_sep2026.xls"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def build_data():
    if not DATA.exists():
        raise FileNotFoundError(f"Place the NHS England workbook at {DATA}")
    activity = pd.read_excel(DATA, sheet_name="Activity", header=13, engine="xlrd")
    performance = pd.read_excel(DATA, sheet_name="Performance", header=13, engine="xlrd")
    activity.columns = [str(c).strip() for c in activity.columns]
    performance.columns = [str(c).strip() for c in performance.columns]
    date_col = "Period"
    activity[date_col] = pd.to_datetime(activity[date_col], errors="coerce")
    performance[date_col] = pd.to_datetime(performance[date_col], errors="coerce")
    act_cols = {
        "Period": "Period", "Total Attendances": "Attendances",
        "Total Emergency Admissions": "EmergencyAdmissions",
        "Number of patients spending >4 hours\n from decision to admit to admission": "WaitOver4HoursAfterDecision",
        "Number of patients spending >12 hours from decision to admit to admission": "WaitOver12HoursAfterDecision"
    }
    perf_cols = {"Period": "Period", "Percentage in 4 hours or less (all)": "Within4HoursRate"}
    act = activity[[c for c in act_cols if c in activity.columns]].rename(columns=act_cols)
    perf = performance[[c for c in perf_cols if c in performance.columns]].rename(columns=perf_cols)
    df = act.merge(perf, on="Period", how="left")
    for c in df.columns:
        if c != "Period": df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Period", "Attendances"]).sort_values("Period")
    df["Year"] = df["Period"].dt.year
    df["Month"] = df["Period"].dt.strftime("%b")
    df["Within4HoursPct"] = df["Within4HoursRate"] * 100
    df["MonthLabel"] = df["Period"].dt.strftime("%b %Y")
    df.to_csv(OUT / "england_monthly_ae.csv", index=False)
    latest = df.iloc[-1]
    recent = df.copy()
    yoy = df[df.Period == (latest.Period - pd.DateOffset(years=1))]
    yoy_delta = None
    if not yoy.empty and pd.notna(yoy.iloc[0]["Attendances"]):
        yoy_delta = round((latest["Attendances"] / yoy.iloc[0]["Attendances"] - 1) * 100, 2)
    payload = {
        "latest_month": latest.Period.strftime("%B %Y"),
        "attendances": int(latest["Attendances"]),
        "emergency_admissions": int(latest["EmergencyAdmissions"]) if pd.notna(latest.get("EmergencyAdmissions")) else None,
        "within4": float(latest["Within4HoursPct"]) if pd.notna(latest.get("Within4HoursPct")) else None,
        "over12h": int(latest["WaitOver12HoursAfterDecision"]) if pd.notna(latest.get("WaitOver12HoursAfterDecision")) else None,
        "yoy_change": yoy_delta,
        "data_start": df.Period.min().strftime("%b %Y"),
        "data_end": df.Period.max().strftime("%b %Y"),
        "series": [{"month": r.Period.strftime("%b %Y"), "date": r.Period.strftime("%Y-%m-%d"),
                    "attendances": int(r.Attendances) if pd.notna(r.Attendances) else None,
                    "admissions": int(r.EmergencyAdmissions) if pd.notna(getattr(r, "EmergencyAdmissions", None)) else None,
                    "within4": round(float(r.Within4HoursPct), 2) if pd.notna(r.Within4HoursPct) else None,
                    "over12h": int(r.WaitOver12HoursAfterDecision) if pd.notna(getattr(r, "WaitOver12HoursAfterDecision", None)) else None}
                   for r in recent.itertuples()],
        "all": [{"year": int(r.Year), "month": r.Month, "within4": round(float(r.Within4HoursPct), 2) if pd.notna(r.Within4HoursPct) else None}
                for r in df.itertuples()]
    }
    (OUT / "dashboard_data.json").write_text(json.dumps(payload, indent=2))
    return payload


def dashboard(d):
    data = json.dumps(d)
    html = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>England A&amp;E | Monthly report</title><script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script><style>
*{box-sizing:border-box}body{margin:0;background:#101310;color:#e6e9e4;font:12px Inter,Arial,Helvetica,sans-serif}.top{height:42px;background:#171a17;border-bottom:1px solid #2b302a;color:#e8ece5;display:flex;align-items:center;justify-content:space-between;padding:0 20px}.brand{font-size:11px;font-weight:700;letter-spacing:.7px}.badge{font-size:10px;color:#abb2a8}.layout{max-width:1500px;margin:0 auto;padding:14px;display:grid;grid-template-columns:202px minmax(0,1fr);gap:12px}.rail{background:#171a17;border:1px solid #2b302a;padding:13px;height:max-content;position:sticky;top:12px}.rail h2{font-size:11px;margin:0 0 9px;color:#e8ece5}.rail h3{font-size:9px;text-transform:uppercase;letter-spacing:.6px;margin:14px 0 5px;color:#b8c0b4}.rail p{font-size:10px;line-height:1.5;color:#a4aaa1;margin:0}.rail .rule{height:1px;background:#30352e;margin:12px 0}.filter-label{font-size:9px;color:#adb4a9;display:block;margin-bottom:5px}.filter{width:100%;background:#222720;border:1px solid #41483d;color:#e6e9e4;padding:8px;font-size:11px;border-radius:3px}.content{min-width:0}.heading{display:flex;justify-content:space-between;align-items:flex-end;margin:0 0 10px}.heading h1{font-size:17px;margin:0 0 3px;color:#eff1ec;font-weight:650}.heading p{font-size:10px;color:#a4aaa1;margin:0}.period{font-size:9px;color:#a4aaa1;text-align:right}.period strong{font-size:11px;color:#e4e8df}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:9px}.card,.panel{background:#171a17;border:1px solid #2b302a;border-radius:3px;min-width:0}.card{padding:10px 11px;border-top:2px solid #a9d936;min-height:72px}.label{font-size:9px;color:#a9b0a5}.value{font-size:19px;font-weight:650;color:#e8ece5;margin-top:5px}.hint{font-size:9px;color:#a9d936;margin-top:3px}.grid{display:grid;grid-template-columns:1.1fr .9fr;gap:9px}.panel{padding:10px 11px}.panel h2{font-size:11px;margin:0;color:#e6e9e4}.panel p{font-size:9px;color:#9da49a;margin:3px 0 0}.chart{height:205px}.foot{font-size:9px;color:#92998f;margin:8px 1px 0}@media(max-width:850px){.layout{grid-template-columns:1fr;padding:10px}.rail{position:static;order:2}.cards{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.top{padding:0 12px}}@media(max-width:480px){.cards{grid-template-columns:1fr}.heading{align-items:flex-start;gap:8px;flex-direction:column}.period{text-align:left}}
</style></head><body><header class="top"><div class="brand">A&amp;E MONTHLY REPORT</div><div class="badge">NHS ENGLAND · NATIONAL SERIES</div></header><main class="layout"><aside class="rail"><h2>Report view</h2><label class="filter-label" for="yearFilter">Reporting year</label><select id="yearFilter" class="filter" aria-label="Filter charts by reporting year"><option value="recent">Latest 24 months</option><option value="all">All available months</option></select><div class="rule"></div><h3>Measure definitions</h3><p>Four-hour performance is the share of attendances admitted, transferred or discharged within four hours. Long waits are patients spending more than 12 hours from decision to admit to admission.</p><h3>Comparability</h3><p>Earlier activity figures are estimates before June 2015. Interpret four-hour comparisons cautiously during the Clinical Review of Standards field-test period, May 2019–May 2023.</p><h3>Source</h3><p>Official NHS England, A&amp;E Attendances and Emergency Admissions monthly time series. England aggregate statistics; not individual hospital or patient records.</p></aside><section class="content"><div class="heading"><div><h1>Accident &amp; emergency activity</h1><p>Monthly activity, four-hour performance and decision-to-admit waits · England</p></div><div class="period">Selected latest period<br><strong id="latestLabel"></strong></div></div><div class="cards"><div class="card"><div class="label">A&amp;E attendances</div><div class="value" id="attendances">—</div><div class="hint" id="yoy">Selected period</div></div><div class="card"><div class="label">Within four hours</div><div class="value" id="within4">—</div><div class="hint">All A&amp;E types</div></div><div class="card"><div class="label">Emergency admissions</div><div class="value" id="admissions">—</div><div class="hint">Through all routes</div></div><div class="card"><div class="label">Over 12h after decision</div><div class="value" id="over12">—</div><div class="hint">Patients · decision-to-admit</div></div></div><div class="grid"><section class="panel"><h2>Monthly attendances</h2><p>Published months · activity estimates before June 2015</p><div id="activity" class="chart"></div></section><section class="panel"><h2>Four-hour performance</h2><p>Share of attendances within four hours</p><div id="performance" class="chart"></div></section><section class="panel"><h2>Patients waiting over 12 hours</h2><p>After decision to admit</p><div id="waits" class="chart"></div></section><section class="panel"><h2>Seasonal performance</h2><p>Four-hour performance by calendar year; blank cells indicate missing data</p><div id="season" class="chart"></div></section></div><div class="foot">Workbook data span: '''+d['data_start']+r'''–'''+d['data_end']+r''' · Four-hour comparisons during May 2019–May 2023 require caution.</div></section></main><script>const D='''+data+r''';const R=D.series;const $=id=>document.getElementById(id);const years=[...new Set(R.map(r=>+r.date.slice(0,4)))].sort((a,b)=>a-b);years.forEach(y=>{const o=document.createElement('option');o.value=y;o.textContent=y;$('yearFilter').appendChild(o)});const base={paper_bgcolor:'#171a17',plot_bgcolor:'#171a17',font:{family:'Arial,sans-serif',color:'#aeb5aa',size:9},margin:{l:54,r:12,t:12,b:43},transition:{duration:350,easing:'cubic-in-out'},xaxis:{gridcolor:'#292e28',zerolinecolor:'#3b4139',tickfont:{size:8},linecolor:'#373d35'},yaxis:{gridcolor:'#292e28',zerolinecolor:'#3b4139',tickfont:{size:8},linecolor:'#373d35'}};const cfg={displayModeBar:false,responsive:true};const months=Array.from({length:12},(_,i)=>new Date(2000,i,1).toLocaleString('en',{month:'short'}));function draw(){const yr=$('yearFilter').value;const rows=yr==='all'?R:yr==='recent'?R.slice(-24):R.filter(x=>x.date.startsWith(yr));const latest=rows[rows.length-1];$('latestLabel').textContent=latest?latest.month:'No data';$('attendances').textContent=latest?.attendances==null?'n/a':latest.attendances.toLocaleString('en-GB');$('within4').textContent=latest?.within4==null?'n/a':latest.within4.toFixed(1)+'%';$('admissions').textContent=latest?.admissions==null?'n/a':latest.admissions.toLocaleString('en-GB');$('over12').textContent=latest?.over12h==null?'n/a':latest.over12h.toLocaleString('en-GB');$('yoy').textContent=yr==='all'?(D.yoy_change==null?'Year-on-year unavailable':`${D.yoy_change>0?'+':''}${D.yoy_change.toFixed(1)}% vs same month last year`):'Latest available month in selected year';const x=rows.map(r=>r.month);Plotly.react('activity',[{type:'scatter',mode:'lines',x,y:rows.map(r=>r.attendances),line:{color:'#b4df43',width:2},hovertemplate:'%{x}<br>%{y:,} attendances<extra></extra>'}],{...base,yaxis:{...base.yaxis,tickformat:',.2s',title:{text:'Attendances',font:{size:9}}},xaxis:{...base.xaxis,tickangle:-35}},cfg);Plotly.react('performance',[{type:'scatter',mode:'lines',x,y:rows.map(r=>r.within4),line:{color:'#b4df43',width:2},hovertemplate:'%{x}<br>%{y:.1f}% within four hours<extra></extra>'},{type:'scatter',mode:'lines',x,y:rows.map(r=>r.within4==null?null:95),line:{color:'#727a70',dash:'dash',width:1},name:'95% standard',hovertemplate:'95% standard<extra></extra>'}],{...base,yaxis:{...base.yaxis,ticksuffix:'%',range:[40,100],title:{text:'Within 4 hours (%)',font:{size:9}}},xaxis:{...base.xaxis,tickangle:-35},showlegend:false},cfg);Plotly.react('waits',[{type:'bar',x,y:rows.map(r=>r.over12h),marker:{color:'#879f57'},hovertemplate:'%{x}<br>%{y:,} patients<extra></extra>'}],{...base,yaxis:{...base.yaxis,tickformat:',.2s',title:{text:'Patients',font:{size:9}}},xaxis:{...base.xaxis,tickangle:-35}},cfg);const heatYears=yr==='all'?years:yr==='recent'?[...new Set(rows.map(a=>+a.date.slice(0,4)))]:[+yr];const z=heatYears.map(y=>months.map(m=>{const r=R.find(a=>+a.date.slice(0,4)===y&&a.month.startsWith(m+' '));return r?.within4??null}));Plotly.react('season',[{type:'heatmap',x:months,y:heatYears,z,colorscale:[[0,'#374237'],[.55,'#788b49'],[1,'#b4df43']],zmin:60,zmax:100,colorbar:{title:'%',thickness:8,len:.8},hovertemplate:'%{y} %{x}<br>%{z:.1f}% within 4h<extra></extra>'}],{...base,margin:{l:48,r:42,t:8,b:25},xaxis:{...base.xaxis,showgrid:false},yaxis:{...base.yaxis,showgrid:false,autorange:'reversed'}},cfg)}$('yearFilter').addEventListener('change',draw);draw();</script></body></html>'''
    (OUT / "dashboard.html").write_text(html, encoding="utf-8")

if __name__ == "__main__":
    dashboard(build_data())
    print(f"Dashboard written to {OUT / 'dashboard.html'}")
