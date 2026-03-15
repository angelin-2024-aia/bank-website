from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone
from collections import Counter

try:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import cross_val_score
    ML_OK = True
except ImportError:
    ML_OK = False

app = Flask(__name__)
CORS(app)

RAW = [
    [85,10,22,2,1,"brute_force"],[90,12,22,3,1,"brute_force"],
    [78,11,22,1,1,"brute_force"],[95,9,22,4,1,"brute_force"],
    [70,14,22,0,1,"brute_force"],[82,10,22,5,1,"brute_force"],
    [88,13,22,23,1,"brute_force"],[75,11,22,2,0,"brute_force"],
    [65,12,22,3,1,"brute_force"],[91,8,22,1,1,"brute_force"],
    [72,10,22,4,0,"brute_force"],[84,9,21,2,1,"brute_force"],
    [3,45,80,14,0,"phishing"],[2,50,443,15,0,"phishing"],
    [4,48,80,11,0,"phishing"],[1,55,443,13,0,"phishing"],
    [3,42,80,16,0,"phishing"],[2,60,443,10,0,"phishing"],
    [5,38,80,9,0,"phishing"],[3,52,443,14,0,"phishing"],
    [4,180,80,10,0,"sql_injection"],[2,220,443,11,0,"sql_injection"],
    [3,195,80,12,0,"sql_injection"],[5,210,3306,9,0,"sql_injection"],
    [2,175,80,14,0,"sql_injection"],[4,230,443,10,0,"sql_injection"],
    [3,200,80,11,0,"sql_injection"],[6,185,8080,12,0,"sql_injection"],
    [1,480,22,9,0,"malware_upload"],[2,520,21,8,0,"malware_upload"],
    [1,600,22,10,0,"malware_upload"],[2,450,80,7,0,"malware_upload"],
    [1,550,22,11,0,"malware_upload"],[2,490,21,9,0,"malware_upload"],
    [1,8,22,14,0,"normal"],[0,5,80,10,0,"normal"],
    [1,7,443,11,0,"normal"],[1,4,22,16,0,"normal"],
    [0,6,80,9,0,"normal"],[1,9,22,15,0,"normal"],
    [1,5,443,12,0,"normal"],[0,7,80,13,0,"normal"],
    [1,6,22,17,0,"normal"],[1,8,443,10,0,"normal"],
]

X_raw = [[r[0],r[1],r[2],r[3],r[4]] for r in RAW]
y_raw = [r[5] for r in RAW]

clf = iso = le = None
cv_score = "N/A"

if ML_OK:
    X = np.array(X_raw)
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    clf.fit(X, y)
    iso = IsolationForest(contamination=0.20, random_state=42)
    iso.fit(X)
    scores = cross_val_score(clf, X, y, cv=5)
    cv_score = f"{scores.mean()*100:.1f}%"
    print(f"[ML] RandomForest CV accuracy : {cv_score}")
    print(f"[ML] Classes : {list(le.classes_)}")

_log = []

def _make_features(data):
    return [
        min(int(data.get("attempts_per_min", 5)), 120),
        min(int(data.get("payload_len", 10)), 600),
        int(data.get("port", 22)),
        datetime.now(timezone.utc).hour,
        1 if data.get("used_known_creds", False) else 0,
    ]

def _rule_classify(f):
    if f[0] > 50: return "brute_force", "anomaly"
    if f[1] > 300: return "malware_upload", "anomaly"
    if f[1] > 100: return "sql_injection", "anomaly"
    if f[2] in (80,443) and f[1] > 25: return "phishing", "normal"
    return "normal", "normal"

@app.route("/health")
def health():
    return jsonify({"status":"ok","ml":ML_OK,"ts":datetime.now(timezone.utc).isoformat()})

@app.route("/classify", methods=["POST"])
def classify():
    data = request.get_json(silent=True) or {}
    feats = _make_features(data)
    if ML_OK:
        fa = np.array([feats])
        label = le.inverse_transform(clf.predict(fa))[0]
        proba = float(max(clf.predict_proba(fa)[0]))
        iso_score = float(iso.decision_function(fa)[0])
        is_anomaly = iso.predict(fa)[0] == -1
        anomaly = "anomaly" if is_anomaly else "normal"
        confidence = round(proba * 100, 1)
    else:
        label, anomaly = _rule_classify(feats)
        iso_score = -0.4 if anomaly == "anomaly" else 0.3
        confidence = 82.0
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": request.remote_addr,
        "attack_type": label,
        "anomaly": anomaly,
        "confidence": confidence,
        "iso_score": round(iso_score, 4),
        "features": feats,
    }
    _log.append(entry)
    if len(_log) > 500:
        _log.pop(0)
    return jsonify({"attack_type":label,"anomaly":anomaly,"confidence":confidence,"iso_score":round(iso_score,4),"timestamp":entry["timestamp"]})

@app.route("/logs")
def get_logs():
    limit = min(int(request.args.get("limit", 50)), 200)
    return jsonify(_log[-limit:][::-1])

@app.route("/stats")
def get_stats():
    if not _log:
        return jsonify({"total":0,"by_type":{},"anomaly_count":0,"anomaly_rate":"0%"})
    by_type = dict(Counter(e["attack_type"] for e in _log))
    an_count = sum(1 for e in _log if e["anomaly"] == "anomaly")
    return jsonify({"total":len(_log),"by_type":by_type,"anomaly_count":an_count,"anomaly_rate":f"{round(an_count/len(_log)*100,1)}%"})

if __name__ == "__main__":
    print("="*50)
    print("  Lurenex ML Server - port 5000")
    print(f"  sklearn: {ML_OK}  |  accuracy: {cv_score}")
    print("="*50)
    app.run(host="0.0.0.0", port=5000, debug=False)
