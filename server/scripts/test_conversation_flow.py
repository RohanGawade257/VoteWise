"""
test_conversation_flow.py — End-to-end test for VoteWise conversational continuity.

Tests the full 6-turn flow:
  GF Turn 1-4 → GF completes → CC activated → followup "what next?" works.

Run from server/ directory:
  python scripts/test_conversation_flow.py
"""
import requests
import json
import sys

BASE = "http://localhost:8080"
URL = f"{BASE}/api/chat"
PASS = "[PASS]"
FAIL = "[FAIL]"

def send(msg, gf=None, cc=None, persona="general"):
    payload = {"message": msg, "persona": persona, "context": "{}"}
    if gf:
        payload["guidedFlow"] = gf
    if cc:
        payload["conversationContext"] = cc
    r = requests.post(URL, json=payload, timeout=30)
    if r.status_code != 200:
        print(f"  HTTP ERROR {r.status_code}: {r.text[:200]}")
        return {}
    return r.json()

def meta(d):
    return d.get("meta", {})

def check(label, condition, got=""):
    status = PASS if condition else FAIL
    print(f"  {status} {label}" + (f" | got: {got}" if not condition else ""))
    return condition

passed = 0
failed = 0

def run(label, cond, got=""):
    global passed, failed
    ok = check(label, cond, got)
    if ok:
        passed += 1
    else:
        failed += 1

print("=" * 60)
print("VoteWise Conversational Context End-to-End Test")
print("=" * 60)

# ── Turn 1: Trigger guided flow ──────────────────────────────────────────────
print("\n[Turn 1] Trigger: 'first time voter'")
r1 = send("first time voter")
m1 = meta(r1)
run("GF triggered (guided_flow_active=True)", m1.get("guided_flow_active") is True, m1.get("guided_flow_active"))
run("GF step is ask_first_time", m1.get("guided_flow_step") == "ask_first_time", m1.get("guided_flow_step"))
gf = {"active": True, "step": m1.get("guided_flow_step"), "state": m1.get("guided_flow_state", {})}

# ── Turn 2: Yes, first time ───────────────────────────────────────────────────
print("\n[Turn 2] Reply: 'yes'")
r2 = send("yes", gf=gf)
m2 = meta(r2)
run("GF advanced to ask_age_status", m2.get("guided_flow_step") == "ask_age_status", m2.get("guided_flow_step"))
gf = {"active": True, "step": m2.get("guided_flow_step"), "state": m2.get("guided_flow_state", {})}

# ── Turn 3: I am 18 ───────────────────────────────────────────────────────────
print("\n[Turn 3] Reply: 'I am already 18'")
r3 = send("I am already 18", gf=gf)
m3 = meta(r3)
run("GF advanced to ask_has_epic", m3.get("guided_flow_step") == "ask_has_epic", m3.get("guided_flow_step"))
gf = {"active": True, "step": m3.get("guided_flow_step"), "state": m3.get("guided_flow_state", {})}

# ── Turn 4: No, no voter ID ───────────────────────────────────────────────────
print("\n[Turn 4] Reply: 'no I don't have one'")
r4 = send("no I don't have one", gf=gf)
m4 = meta(r4)
run("GF reached terminal show_path_no_epic", m4.get("guided_flow_step") == "show_path_no_epic", m4.get("guided_flow_step"))
run("GF still active (not yet complete)", m4.get("guided_flow_active") is True, m4.get("guided_flow_active"))
gf = {"active": True, "step": m4.get("guided_flow_step"), "state": m4.get("guided_flow_state", {})}
print(f"  GF state flow_type: {m4.get('guided_flow_state', {}).get('flow_type')}")

# ── Turn 5: User replies to terminal step → GF completes, CC activates ────────
print("\n[Turn 5] Reply to terminal step: 'explain form 6' (GF complete, CC should activate)")
r5 = send("explain form 6", gf=gf)
m5 = meta(r5)
cc5 = m5.get("conversation_context", {})
run("CC active after GF completes", m5.get("conversation_context_active") is True or cc5.get("active") is True,
    f"conversation_context_active={m5.get('conversation_context_active')} cc.active={cc5.get('active')}")
run("CC has last_topic set", cc5.get("last_topic") is not None, cc5.get("last_topic"))
run("CC has flow_type", cc5.get("flow_type") is not None, cc5.get("flow_type"))
print(f"  Answer (first 100): {r5.get('answer', '')[:100]}")
print(f"  CC last_topic: {cc5.get('last_topic')}")

# ── Turn 6: "What next?" must use CC, not out-of-scope ────────────────────────
print("\n[Turn 6] Follow-up: 'what should I do next?' (MUST use CC, not out-of-scope)")
r6 = send("what should I do next?", cc=cc5)
m6 = meta(r6)
answer6 = r6.get("answer", "")
is_not_oos = "civic education" not in answer6 and "can't help" not in answer6.lower()
run("Not out-of-scope response", is_not_oos, answer6[:80])
run("Intent is contextual_followup OR civic_static (not out_of_scope)", m6.get("intent") in {"contextual_followup", "civic_static", "first_time_voter_guided"}, m6.get("intent"))
print(f"  Answer (first 160): {answer6[:160]}")
print(f"  Intent: {m6.get('intent')}")
print(f"  Last topic: {m6.get('last_topic')}")

# ── Turn 7: Out-of-scope should still be blocked ─────────────────────────────
print("\n[Turn 7] Sanity: 'What is the capital of France?' (should be OOS)")
r7 = send("What is the capital of France?")
m7 = meta(r7)
answer7 = r7.get("answer", "")
oos_words = {"civic", "election", "voter", "register", "eci"}
is_oos = m7.get("intent") == "out_of_scope" or any(w in answer7.lower() for w in oos_words)
run("Out-of-scope correctly identified", is_oos, f"intent={m7.get('intent')}")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
total = passed + failed
print(f"Results: {passed}/{total} tests passed")
if failed > 0:
    print("Some tests FAILED. Review the output above.")
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
