import json, time, argparse, requests
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

LOG_FILE     = Path(__file__).parent / "cowrie_logs.json"
RESULTS_FILE = Path(__file__).parent / "processed_results.json"
ML_API       = "http://127.0.0.1:5000/classify"

def extract_features(events):
    ip_map = {}
    for e in events:
        ip = e.get("source_ip", "unknown")
        if ip not in ip_map:
            ip_map[ip] = {"attempts":0,"commands":0,"usernames":[],"passwords":[],"payloads":[],"first_seen":e["timestamp"],"last_seen":e["timestamp"]}
        d = ip_map[ip]
        if e["timestamp"] > d["last_seen"]: d["last_seen"] = e["timestamp"]
        if e["event_type"] in ("login_failed","login_success"):
            d["attempts"] += 1
            if e.get("username"): d["usernames"].append(e["username"])
            if e.get("password"): d["passwords"].append(e["password"])
        if e["event_type"] == "command":
            d["commands"] += 1
            if e.get("command"): d["payloads"].append(e["command"])
    return ip_map

def classify_ip(ip, data):
    avg_payload = sum(len(p) for p in data["payloads"]) // len(data["payloads"]) if data["payloads"] else 0
    known_creds = any(u in ("root","admin","staff","angel","ubuntu","pi") for u in data["usernames"])
    try:
        r = requests.post(ML_API, json={"attempts_per_min":min(data["attempts"],120),"payload_len":avg_payload,"port":22,"used_known_creds":known_creds}, timeout=3)
        res = r.json()
    except:
        at = data["attempts"]
        res = {"attack_type":"brute_force" if at>20 else "normal","anomaly":"anomaly" if at>20 else "normal","confidence":80.0}
    return {"ip":ip,"attempts":data["attempts"],"commands":data["commands"],"unique_users":len(set(data["usernames"])),"unique_pwds":len(set(data["passwords"])),"first_seen":data["first_seen"],"last_seen":data["last_seen"],"attack_type":res.get("attack_type","unknown"),"anomaly":res.get("anomaly","normal"),"confidence":res.get("confidence",0),"top_commands":list(Counter(data["payloads"]).most_common(3)),"processed_at":datetime.now(timezone.utc).isoformat()}

def summarize(results):
    total = len(results)
    anomalies = sum(1 for r in results if r["anomaly"] == "anomaly")
    return {"total_ips":total,"anomaly_ips":anomalies,"normal_ips":total-anomalies,"by_attack_type":dict(Counter(r["attack_type"] for r in results)),"top_attackers":sorted(results,key=lambda r:r["attempts"],reverse=True)[:5],"generated_at":datetime.now(timezone.utc).isoformat()}

def process_once():
    if not LOG_FILE.exists():
        print(f"[LOG] cowrie_logs.json not found — run cowrie_sim.py first")
        return
    raw = json.loads(LOG_FILE.read_text(encoding="utf-8"))
    ip_map = extract_features(raw)
    print(f"[LOG] {len(raw)} events  ->  {len(ip_map)} unique IPs")
    results = []
    for ip, data in ip_map.items():
        r = classify_ip(ip, data)
        tag = "ANOMALY" if r["anomaly"] == "anomaly" else "normal"
        print(f"  [{tag}]  {ip:22s}  attempts={r['attempts']:3d}  type={r['attack_type']}")
        results.append(r)
    summary = summarize(results)
    RESULTS_FILE.write_text(json.dumps({"summary":summary,"results":results}, indent=2), encoding="utf-8")
    print(f"[LOG] Anomalies: {summary['anomaly_ips']} / {summary['total_ips']}  -> saved")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    if args.watch:
        print("[LOG] Watch mode — processing every 15s")
        while True:
            process_once()
            time.sleep(15)
    else:
        process_once()

if __name__ == "__main__":
    main()
