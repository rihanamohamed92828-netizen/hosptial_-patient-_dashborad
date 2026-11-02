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
    recent = df.tail(24).copy()
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
    yoy = (f"{d['yoy_change']:+.1f}% vs same month last year" if d["yoy_change"] is not None else "Year-on-year comparison unavailable")
    within = f"{d['within4']:.1f}%" if d["within4"] is not None else "n/a"
    over12 = f"{d['over12h']:,}" if d["over12h"] is not None else "n/a"
    html = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>England A&E | Monthly report</title><script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script><style>
*{box-sizing:border-box}body{margin:0;background:#e9ecef;color:#26323d;font:12px Arial,Helvetica,sans-serif}.top{height:42px;background:#17324d;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 22px}.brand{font-size:12px;font-weight:700;letter-spacing:.2px}.badge{font-size:10px}.layout{max-width:1440px;margin:0 auto;padding:16px 20px;display:grid;grid-template-columns:205px minmax(0,1fr);gap:15px}.rail{background:#fff;border:1px solid #cbd1d6;padding:14px;height:max-content}.rail h2{font-size:12px;margin:0 0 10px;color:#263849}.rail h3{font-size:10px;margin:15px 0 4px;color:#33495b}.rail p{font-size:10px;line-height:1.45;color:#5f6b75;margin:0}.rail .rule{height:1px;background:#d8dde1;margin:13px 0}.content{min-width:0}.heading{display:flex;justify-content:space-between;align-items:flex-end;margin:0 0 10px}.heading h1{font-size:19px;margin:0 0 4px;color:#263849}.heading p{font-size:11px;color:#596671;margin:0}.period{font-size:10px;color:#4f5e69;text-align:right}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-bottom:10px}.card,.panel{background:#fff;border:1px solid #cbd1d6;border-radius:0;box-shadow:none}.card{padding:10px 12px;border-top:2px solid #315f85;min-height:77px}.label{font-size:10px;color:#5a6670}.value{font-size:21px;font-weight:700;color:#263849;margin-top:5px}.hint{font-size:9px;color:#68737c;margin-top:3px}.grid{display:grid;grid-template-columns:1.1fr .9fr;gap:10px}.panel{padding:10px 12px;min-width:0}.panel h2{font-size:12px;margin:0;color:#263849}.panel p{font-size:10px;color:#66717b;margin:3px 0 0}.chart{height:205px}.foot{font-size:9px;color:#69747d;margin:8px 1px 0}@media(max-width:850px){.layout{grid-template-columns:1fr;padding:12px}.rail{order:2}.cards{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.top{padding:0 14px}}@media(max-width:480px){.cards{grid-template-columns:1fr}.heading{align-items:flex-start;gap:8px;flex-direction:column}.period{text-align:left}}
</style></head><body><header class="top"><div class="brand">A&amp;E MONTHLY REPORT</div><div class="badge">NHS ENGLAND · NATIONAL SERIES</div></header><main class="layout"><aside class="rail"><h2>Report notes</h2><p>England-level monthly activity and performance. Latest reporting period shown at right.</p><div class="rule"></div><h3>Measure definitions</h3><p>Four-hour performance is the share of attendances admitted, transferred or discharged within four hours. Long waits are patients spending more than 12 hours from decision to admit to admission.</p><h3>Comparability</h3><p>Earlier activity figures are estimates before June 2015. Interpret four-hour comparisons cautiously during the Clinical Review of Standards field-test period, May 2019–May 2023.</p><h3>Source</h3><p>NHS England, A&amp;E Attendances and Emergency Admissions monthly time series. Aggregate statistics, not individual hospital or patient records.</p></aside><section class="content"><div class="heading"><div><h1>Accident &amp; emergency activity</h1><p>Activity, four-hour performance and decision-to-admit waits</p></div><div class="period">Latest period<br><strong>'''+d['latest_month']+r'''</strong></div></div><div class="cards"><div class="card"><div class="label">A&amp;E attendances</div><div class="value">'''+f'''{d['attendances']:,}'''+r'''</div><div class="hint">'''+yoy+r'''</div></div><div class="card"><div class="label">Within four hours</div><div class="value">'''+within+r'''</div><div class="hint">All A&amp;E types</div></div><div class="card"><div class="label">Emergency admissions</div><div class="value">'''+(f"{d['emergency_admissions']:,}" if d['emergency_admissions'] is not None else 'n/a')+r'''</div><div class="hint">Through all routes</div></div><div class="card"><div class="label">Over 12h after decision</div><div class="value">'''+over12+r'''</div><div class="hint">Decision-to-admit measure</div></div></div><div class="grid"><section class="panel"><h2>Monthly attendances</h2><p>Latest 24 published months · England</p><div id="activity" class="chart"></div></section><section class="panel"><h2>Four-hour performance</h2><p>Share of attendances within four hours</p><div id="performance" class="chart"></div></section><section class="panel"><h2>Patients waiting over 12 hours</h2><p>After decision to admit · latest 24 months</p><div id="waits" class="chart"></div></section><section class="panel"><h2>Seasonal performance</h2><p>Four-hour performance by calendar year; blank cells are missing data</p><div id="season" class="chart"></div></section></div><div class="foot">Data span in workbook: '''+d['data_start']+r'''–'''+d['data_end']+r''' · Operational context, not clinical guidance.</div></section></main><script>const D='''+data+r''';const R=D.series;const base={paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{family:'Arial, sans-serif',color:'#505c66',size:9},margin:{l:54,r:12,t:20,b:45},xaxis:{gridcolor:'#e2e5e8',zerolinecolor:'#c7ccd1',tickfont:{size:8}},yaxis:{gridcolor:'#e2e5e8',zerolinecolor:'#c7ccd1',tickfont:{size:8}}};const cfg={displayModeBar:false,responsive:true};Plotly.newPlot('activity',[{type:'scatter',mode:'lines',x:R.map(x=>x.month),y:R.map(x=>x.attendances),line:{color:'#315f85',width:2},hovertemplate:'%{x}<br>%{y:,} attendances<extra></extra>'}],{...base,yaxis:{...base.yaxis,tickformat:',.2s',title:{text:'Attendances',font:{size:9}}},xaxis:{...base.xaxis,tickangle:-35}},cfg);Plotly.newPlot('performance',[{type:'scatter',mode:'lines',name:'Observed',x:R.map(x=>x.month),y:R.map(x=>x.within4),line:{color:'#27836c',width:2},hovertemplate:'%{x}<br>%{y:.1f}% within four hours<extra></extra>'},{type:'scatter',mode:'lines',x:R.map(x=>x.month),y:R.map(x=>x.within4===null?null:95),line:{color:'#87919a',dash:'dash',width:1},name:'95% standard',hovertemplate:'95% standard<extra></extra>'}],{...base,yaxis:{...base.yaxis,ticksuffix:'%',range:[40,100],title:{text:'Within 4 hours (%)',font:{size:9}}},xaxis:{...base.xaxis,tickangle:-35},legend:{orientation:'h',y:1.2,x:0,font:{size:8}}},cfg);Plotly.newPlot('waits',[{type:'bar',x:R.map(x=>x.month),y:R.map(x=>x.over12h),marker:{color:'#315f85'},hovertemplate:'%{x}<br>%{y:,} patients<extra></extra>'}],{...base,yaxis:{...base.yaxis,tickformat:',.2s',title:{text:'Patients',font:{size:9}}},xaxis:{...base.xaxis,tickangle:-35}},cfg);const years=[...new Set(D.all.map(x=>x.year))];const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];const z=years.map(y=>months.map(m=>{const r=D.all.find(a=>a.year===y&&a.month===m);return r&&r.within4!==null?r.within4:null}));Plotly.newPlot('season',[{type:'heatmap',x:months,y:years,z:z,colorscale:[[0,'#dce6ec'],[.55,'#a8c3d2'],[1,'#27836c']],zmin:60,zmax:100,colorbar:{title:'%',thickness:9,len:.8},hovertemplate:'%{y} %{x}<br>%{z:.1f}% within 4h<extra></extra>'}],{...base,margin:{l:48,r:42,t:8,b:25},xaxis:{...base.xaxis,showgrid:false},yaxis:{...base.yaxis,showgrid:false,autorange:'reversed'}},cfg);</script></body></html>'''
    (OUT / "dashboard.html").write_text(html, encoding="utf-8")

if __name__ == "__main__":
    dashboard(build_data())
    print(f"Dashboard written to {OUT / 'dashboard.html'}")
