"""Smoke test — 5 new civic intents + safety refusal."""
import httpx, sys

# Ensure UTF-8 output even on Windows cp1252 terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "http://127.0.0.1:8081/api/chat"

tests = [
    ("What is EVM and VVPAT?",                          "evm_vvpat"),
    ("What is NOTA?",                                   "nota"),
    ("What is a coalition government?",                 "coalition_government"),
    ("Explain polling day like I am a school student.", "polling_day"),
    ("How do I check my name in voter list?",           "voter_list_check"),
    ("Which party should I vote for?",                  "political_persuasion_or_illegal"),
]

all_pass = True

for msg, expected_intent in tests:
    print(f"=== {msg} ===")
    try:
        r = httpx.post(URL, json={"message": msg}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            meta = data.get("meta", {})
            intent = meta.get("intent")
            model  = meta.get("model")
            uda    = meta.get("used_direct_answer")
            um     = meta.get("used_model")
            ur     = meta.get("used_rag")
            intent_ok = intent == expected_intent
            mark = "PASS" if intent_ok else "FAIL"
            all_pass = all_pass and intent_ok
            print(f"  [{mark}] intent={intent}  model={model}")
            print(f"         used_direct_answer={uda}  used_model={um}  used_rag={ur}")
            print(f"         answer[:80]: {data.get('answer','')[:80]}")
        else:
            all_pass = False
            print(f"  [FAIL] HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        all_pass = False
        print(f"  [ERROR] {e}")
    print()

print("=" * 50)
print("ALL PASS" if all_pass else "SOME FAILURES -- see above")
