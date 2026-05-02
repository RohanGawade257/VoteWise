"""
Full suggested-reply integrity tests for VoteWise.

Run from repo root:
    python server/scripts/test_all_suggested_replies.py
"""
from __future__ import annotations

import asyncio
from pathlib import Path
import sys


SERVER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVER_ROOT.parent
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app.models import ChatRequest
from app.services.smart_chat_orchestrator import generate_smart_response
from app.services.suggested_reply_registry import all_registered_options, registry_entries


PASS = "PASS"
FAIL = "FAIL"


def preview(text: str, limit: int = 110) -> str:
    one_line = " ".join((text or "").split())
    return one_line[:limit] + ("..." if len(one_line) > limit else "")


def suggestion_dict(reply) -> dict:
    if isinstance(reply, dict):
        return reply
    if hasattr(reply, "model_dump"):
        return reply.model_dump()
    return {}


def print_option(label: str, intent: str, domain: str, source: str, ok: bool, issue: str = "") -> None:
    print(f"{label} | {intent} | {domain} | {source} | {PASS if ok else FAIL} | {issue}")


def useful_answer(response) -> bool:
    lower = response.answer.lower()
    bad = ("i can't help with that", "cannot help with that", "outside votewise")
    return bool(response.answer.strip()) and not any(text in lower for text in bad)


def has_stale_flow_suggestions(response) -> bool:
    stale_intents = {
        "guided_yes_first_time",
        "age_already_18",
        "age_turning_18_soon",
        "age_under_18",
        "epic_yes",
        "epic_no",
        "documents_id",
        "explain_step_1",
        "check_name",
        "check_name_how",
    }
    return any(suggestion_dict(reply).get("intent") in stale_intents for reply in response.meta.suggested_replies)


async def test_registry_coverage() -> tuple[int, int]:
    passed = 0
    failed = 0
    print("\nTEST 1 - Registry coverage")
    for item in registry_entries():
        missing = [
            name for name, value in {
                "label": item.label,
                "intent": item.intent,
                "domain": item.domain,
                "handler_type": item.handler_type,
                "fallback_behavior": item.fallback_behavior,
            }.items()
            if not value
        ]
        ok = not missing
        passed += int(ok)
        failed += int(not ok)
        print_option(item.label, item.intent, item.domain, "registry", ok, ", ".join(missing))
    return passed, failed


async def test_handler_coverage() -> tuple[int, int]:
    passed = 0
    failed = 0
    print("\nTEST 2 - Handler coverage")
    for row in all_registered_options():
        label = row["label"]
        intent = row["intended_intent"]
        domain = row["intended_domain"]
        response = await generate_smart_response(ChatRequest(
            message=label,
            persona="general",
            suggestionIntent=intent,
            suggestionDomain=domain,
        ))
        ok = response.meta.answer_source != "out_of_scope" and useful_answer(response)
        issue = "" if ok else preview(response.answer)
        passed += int(ok)
        failed += int(not ok)
        print_option(label, intent, domain, response.meta.answer_source, ok, issue)
    return passed, failed


async def test_context_required_options() -> tuple[int, int]:
    passed = 0
    failed = 0
    print("\nTEST 3 - Context-required options")

    no_context_step = await generate_smart_response(ChatRequest(
        message="Explain Step 1",
        persona="general",
        suggestionIntent="explain_step_1",
        suggestionDomain="voter_registration",
    ))
    ok = no_context_step.meta.answer_source != "out_of_scope" and "which journey" in no_context_step.answer.lower()
    passed += int(ok)
    failed += int(not ok)
    print_option("Explain Step 1 without context", "explain_step_1", "voter_registration", no_context_step.meta.answer_source, ok, preview(no_context_step.answer))

    r1 = await generate_smart_response(ChatRequest(message="Guide me as a first-time voter", persona="general"))
    gf = {"active": True, "step": r1.meta.guided_flow_step, "state": r1.meta.guided_flow_state}
    r2 = await generate_smart_response(ChatRequest(message="Yes, first time", persona="general", guidedFlow=gf))
    gf = {"active": True, "step": r2.meta.guided_flow_step, "state": r2.meta.guided_flow_state}
    r3 = await generate_smart_response(ChatRequest(message="I am already 18", persona="general", guidedFlow=gf))
    gf = {"active": True, "step": r3.meta.guided_flow_step, "state": r3.meta.guided_flow_state}
    r4 = await generate_smart_response(ChatRequest(message="I do not have voter ID", persona="general", guidedFlow=gf))
    gf = {"active": True, "step": r4.meta.guided_flow_step, "state": r4.meta.guided_flow_state}

    with_context_step = await generate_smart_response(ChatRequest(
        message="Explain Step 1",
        persona="general",
        guidedFlow=gf,
        suggestionIntent="explain_step_1",
        suggestionDomain="voter_registration",
    ))
    ok = with_context_step.meta.answer_source != "out_of_scope" and "step 1" in with_context_step.answer.lower()
    passed += int(ok)
    failed += int(not ok)
    print_option("Explain Step 1 with context", "explain_step_1", "voter_registration", with_context_step.meta.answer_source, ok, preview(with_context_step.answer))

    no_context_next = await generate_smart_response(ChatRequest(
        message="What should I do next?",
        persona="general",
        suggestionIntent="continue_next",
        suggestionDomain="voter_registration",
    ))
    ok = no_context_next.meta.answer_source != "out_of_scope" and "which journey" in no_context_next.answer.lower()
    passed += int(ok)
    failed += int(not ok)
    print_option("What should I do next without context", "continue_next", "voter_registration", no_context_next.meta.answer_source, ok, preview(no_context_next.answer))

    with_context_next = await generate_smart_response(ChatRequest(
        message="What should I do next?",
        persona="general",
        guidedFlow=gf,
        suggestionIntent="continue_next",
        suggestionDomain="voter_registration",
    ))
    ok = with_context_next.meta.answer_source != "out_of_scope" and useful_answer(with_context_next)
    passed += int(ok)
    failed += int(not ok)
    print_option("What should I do next with context", "continue_next", "voter_registration", with_context_next.meta.answer_source, ok, preview(with_context_next.answer))
    return passed, failed


async def test_cleanup_flows() -> tuple[int, int]:
    passed = 0
    failed = 0
    print("\nTEST 4 - Out-of-scope cleanup")
    r1 = await generate_smart_response(ChatRequest(message="Guide me as a first-time voter", persona="general"))
    gf = {"active": True, "step": r1.meta.guided_flow_step, "state": r1.meta.guided_flow_state}
    r2 = await generate_smart_response(ChatRequest(message="Yes, first time", persona="general", guidedFlow=gf))
    gf = {"active": True, "step": r2.meta.guided_flow_step, "state": r2.meta.guided_flow_state}
    r3 = await generate_smart_response(ChatRequest(message="what is Python", persona="general", guidedFlow=gf))
    ok = r3.meta.answer_source == "out_of_scope" and not has_stale_flow_suggestions(r3)
    passed += int(ok)
    failed += int(not ok)
    print_option("Guide -> Yes -> what is Python", "out_of_scope_cleanup", "out_of_scope", r3.meta.answer_source, ok, preview(r3.answer))

    print("\nTEST 5 - Safety cleanup")
    safety = await generate_smart_response(ChatRequest(message="Which party should I vote for?", persona="general"))
    ok = safety.meta.answer_source == "safety_refusal" and not has_stale_flow_suggestions(safety)
    passed += int(ok)
    failed += int(not ok)
    print_option("Which party should I vote for?", "safety_cleanup", "unsafe", safety.meta.answer_source, ok, preview(safety.answer))
    return passed, failed


def test_ui_payload_compatibility() -> tuple[int, int]:
    print("\nTEST 6 - UI payload compatibility")
    use_chat = (REPO_ROOT / "client" / "src" / "hooks" / "useChat.js").read_text(encoding="utf-8")
    chat_page = (REPO_ROOT / "client" / "src" / "pages" / "ChatPage.jsx").read_text(encoding="utf-8")
    checks = {
        "suggestionIntent": "suggestionIntent" in use_chat,
        "suggestionDomain": "suggestionDomain" in use_chat,
        "conversationContext": "conversationContext" in use_chat,
        "guidedFlow": "guidedFlow" in use_chat,
        "persona": "persona" in use_chat,
        "latest assistant only": "messageIndex === lastAssistantIdx" in chat_page,
    }
    passed = 0
    failed = 0
    for label, ok in checks.items():
        passed += int(ok)
        failed += int(not ok)
        print_option(label, "ui_payload", "frontend", "source_scan", ok, "" if ok else "missing")
    return passed, failed


async def main() -> int:
    total_passed = 0
    total_failed = 0
    print("=" * 110)
    print("VoteWise Suggested Reply Integrity Tests")
    print("=" * 110)
    print("label | intent | domain | response_source | pass/fail | issue")

    for runner in (
        test_registry_coverage,
        test_handler_coverage,
        test_context_required_options,
        test_cleanup_flows,
    ):
        passed, failed = await runner()
        total_passed += passed
        total_failed += failed

    passed, failed = test_ui_payload_compatibility()
    total_passed += passed
    total_failed += failed

    print("\n" + "=" * 110)
    print(f"Results: {total_passed}/{total_passed + total_failed} passed")
    print("=" * 110)
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
