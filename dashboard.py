import json
from pathlib import Path
from collections import Counter
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

ML_URL    = "http://127.0.0.1:5000"
BANK_URL  = "http://127.0.0.1:5001"
RESULTS_F = Path(__file__).parent / "logs" / "processed_results.json"

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Lurenex Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#020617;--card:#0f172a;--bd:#1e293b;--g:#00ff9d;--r:#ef4444;--b:#3b82f6;--y:#f59e0b;--t:#e2e8f0;--m:#64748b}
body{background:var(--bg);color:var(--t);font-family:'Segoe UI',sans-serif}
header{background:var(--card);border-bottom:1px solid var(--bd);padding:14px 28px;display:flex;justify-content:space-between;align-items:center}
header h1{font-size:1.1rem;color:var(--g);letter-spacing:2px;font-weight:700}
.hright{display:flex;gap:14px;align-items:center;font-size:12px}
.pill{padding:3px 10px;border-radius:20px;font-size:10px;font-weight:700}
.ok{background:rgba(0,255,157,.15);color:var(--g)}.err{background:rgba(239,68,68,.15);color:var(--r)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;padding:18px 22px 0}
.sc{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:18px}
.sc .lbl{font-size:10px;color:var(--m);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.sc .val{font-size:2rem;font-weight:700}.sc .sub{font-size:11px;color:var(--m);margin-top:3px}
.cg{color:var(--g)}.cr{color:var(--r)}.cb{color:var(--b)}.cy{color:var(--y)}
.r2{display:grid;grid-template-columns:2fr 1fr;gap:14px;padding:14px 22px 0}
.r3{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px 22px 16px}
.panel{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:18px}
.panel h3{font-size:10px;color:var(--m);text-transform:uppercase;letter-spacing:1px;margin-bottom:14px}
canvas{max-height:200px}
#feed{height:270px;overflow-y:auto;display:flex;flex-direction:column;gap:5px}
.ev{display:flex;align-items:center;gap:8px;padding:7px 10px;background:rgba(255,255,255,.03);border-radius:7px;font-size:11px;font-family:monospace;flex-shrink:0}
.ba{padding:2px 7px;border-radius:8px;font-size:10px;font-weight:700;background:rgba(239,68,68,.18);color:var(--r);flex-shrink:0}
.bn{padding:2px 7px;border-radius:8px;font-size:10px;font-weight:700;background:rgba(0,255,157,.1);color:var(--g);flex-shrink:0}
.eip{color:var(--b);min-width:115px}.ety{color:var(--y);min-width:110px}.ets{color:var(--m);margin-left:auto}
#topips{height:195px;overflow-y:auto;display:flex;flex-direction:column;gap:5px}
.ipr{display:flex;align-items:center;padding:7px 10px;background:rgba(255,255,255,.03);border-radius:7px;font-size:11px;gap:8px}
.ibw{flex:1;height:3px;background:var(--bd);border-radius:2px}.ibf{height:100%;background:var(--r);border-radius:2px;transition:width .4s}
footer{text-align:center;padding:14px;color:var(--m);font-size:10px}
</style>
</head>
<body>
<header>
  <h1>LURENEX - HONEYPOT MONITORING</h1>
  <div class="hright">
    <span id="ml-pill" class="pill err">ML X</span>
    <span id="bank-pill" class="pill err">BANK X</span>
    <span id="clock" style="font-family:monospace">--:--:--</span>
  </div>
</header>
<div class="stats">
  <div class="sc"><div class="lbl">Total Events</div><div class="val cb" id="s-total">-</div><div class="sub">classified by RandomForest</div></div>
  <div class="sc"><div class="lbl">Anomalies</div><div class="val cr" id="s-anomaly">-</div><div class="sub">flagged by IsolationForest</div></div>
  <div class="sc"><div class="lbl">Brute-Force</div><div class="val cy" id="s-brute">-</div><div class="sub">SSH login attacks</div></div>
  <div class="sc"><div class="lbl">Bank Traps</div><div class="val cg" id="s-bank">-</div><div class="sub">caught by honeypot</div></div>
</div>
<div class="r2">
  <div class="panel"><h3>Live Attack Feed</h3><div id="feed"><div class="ev" style="color:var(--m)">Waiting...</div></div></div>
  <div class="panel"><h3>Attack Type Breakdown</h3><canvas id="donut"></canvas></div>
</div>
<div class="r3">
  <div class="panel"><h3>Anomaly Timeline</h3><canvas id="bar"></canvas></div>
  <div class="panel"><h3>Top Attacking IPs</h3><div id="topips"><div style="color:var(--m);font-size:12px">No data yet</div></div></div>
</div>
<footer>Lurenex - P-2024-28-CS-116 - Cyber Security Lab - SoI Prototype 2026</footer>
<script>
const COLORS=['#ef4444','#f59e0b','#3b82f6','#8b5cf6','#00ff9d'];
const donut=new Chart(document.getElementById('donut').getContext('2d'),{type:'doughnut',data:{labels:[],datasets:[{data:[],backgroundColor:COLORS,borderWidth:0}]},options:{plugins:{legend:{labels:{color:'#94a3b8',font:{size:10}}}},cutout:'68%'}});
const bar=new Chart(document.getElementById('bar').getContext('2d'),{type:'bar',data:{labels:[],datasets:[{label:'Anomaly',data:[],backgroundColor:'#ef4444'},{label:'Normal',data:[],backgroundColor:'#00ff9d33'}]},options:{plugins:{legend:{labels:{color:'#94a3b8',font:{size:10}}}},scales:{x:{stacked:true,ticks:{color:'#64748b',maxRotation:0,font:{size:9}}},y:{stacked:true,ticks:{color:'#64748b'},grid:{color:'#1e293b'}}}}});
let seen=new Set();
async function refresh(){
  try{const s=await(await fetch('/data/ml-stats')).json();document.getElementById('s-total').textContent=s.total??'-';document.getElementById('s-anomaly').textContent=s.anomaly_count??'-';document.getElementById('s-brute').textContent=(s.by_type||{}).brute_force??0;if(Object.keys(s.by_type||{}).length){donut.data.labels=Object.keys(s.by_type);donut.data.datasets[0].data=Object.values(s.by_type);donut.update();}document.getElementById('ml-pill').className='pill ok';document.getElementById('ml-pill').textContent='ML OK';}catch{document.getElementById('ml-pill').className='pill err';}
  try{const evs=await(await fetch('/data/ml-logs')).json();const feed=document.getElementById('feed');for(const ev of evs){const id=ev.timestamp+ev.source_ip;if(seen.has(id))continue;seen.add(id);const d=document.createElement('div');d.className='ev';const ts=(ev.timestamp||'').replace('T',' ').substring(0,19);const an=ev.anomaly==='anomaly';d.innerHTML=`<span class="${an?'ba':'bn'}">${an?'ANOMALY':'NORMAL'}</span><span class="eip">${ev.source_ip||'?'}</span><span class="ety">${ev.attack_type||'?'}</span><span style="color:#94a3b8">${(ev.confidence??0).toFixed(0)}%</span><span class="ets">${ts}</span>`;if(feed.firstChild?.style?.color)feed.innerHTML='';feed.insertBefore(d,feed.firstChild);while(feed.children.length>60)feed.removeChild(feed.lastChild);}const sl=evs.slice(0,20).reverse();bar.data.labels=sl.map(e=>(e.timestamp||'').substring(11,19));bar.data.datasets[0].data=sl.map(e=>e.anomaly==='anomaly'?1:0);bar.data.datasets[1].data=sl.map(e=>e.anomaly==='normal'?1:0);bar.update();}catch{}
  try{const b=await(await fetch('/data/bank-attacks')).json();document.getElementById('s-bank').textContent=b.total??'-';const wrap=document.getElementById('topips');const ips=b.top_ips||[];if(ips.length){const mx=ips[0].attempts||1;wrap.innerHTML=ips.map(ip=>`<div class="ipr"><span style="color:var(--b);font-family:monospace;min-width:130px">${ip.ip}</span><div class="ibw"><div class="ibf" style="width:${Math.round(ip.attempts/mx*100)}%"></div></div><span style="color:var(--r)">${ip.attempts}</span></div>`).join('');}document.getElementById('bank-pill').className='pill ok';document.getElementById('bank-pill').textContent='BANK OK';}catch{document.getElementById('bank-pill').className='pill err';}
}
setInterval(()=>{document.getElementById('clock').textContent=new Date().toTimeString().substring(0,8);},1000);
setInterval(refresh,4000);
window.onload=refresh;
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/data/ml-stats")
def ml_stats():
    try: return jsonify(requests.get(f"{ML_URL}/stats",timeout=2).json())
    except: return jsonify({"total":0,"anomaly_count":0,"by_type":{}})

@app.route("/data/ml-logs")
def ml_logs():
    try: return jsonify(requests.get(f"{ML_URL}/logs?limit=60",timeout=2).json())
    except: return jsonify([])

@app.route("/data/bank-attacks")
def bank_attacks():
    try:
        data=requests.get(f"{BANK_URL}/api/attack-log",timeout=2).json()
        ctr=Counter(e.get("ip","?") for e in data)
        return jsonify({"total":len(data),"top_ips":[{"ip":ip,"attempts":cnt} for ip,cnt in ctr.most_common(6)]})
    except: return jsonify({"total":0,"top_ips":[]})

@app.route("/data/log-results")
def log_results():
    if RESULTS_F.exists():
        try: return jsonify(json.loads(RESULTS_F.read_text(encoding="utf-8")))
        except: pass
    return jsonify({})

if __name__ == "__main__":
    print("="*50)
    print("  Lurenex Dashboard - http://localhost:8000")
    print("="*50)
    app.run(host="0.0.0.0", port=8000, debug=False)
