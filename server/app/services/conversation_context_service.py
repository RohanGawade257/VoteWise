import re
from typing import Dict, Any, Optional
from app.utils.logging import get_logger
from app.services.tone_service import apply_tone_to_template, get_persona_suggested_replies

logger = get_logger("conversation_context")

_FOLLOWUP_INTENTS = {
    "continue_next": [
        r"\bwhat(\s*is|\s*to\s*do)?\s*next\b",
        r"\bwhat\s*should\s*i\s*do\s*next\b",
        r"\bnext\s*step\b",
        r"\bcontinue\b",
        r"\bafter\s*this\b",
        r"\bwhat\s*after\s*this\b",
        r"\btell\s*me\s*(the\s*)?next\s*step\b",
        r"^\s*next\s*$"
    ],
    "explain_current": [
        r"\bexplain\s*more\b",
        r"\bexplain\s*this\b",
        r"\bwhat\s*does\s*this\s*mean\b",
        r"\btell\s*me\s*more\b",
        r"\bhow\s*does\s*this\s*work\b",
    ],
    "where_to_do": [
        r"\bwhere\s*do\s*i\s*do\s*this\b",
        r"\bwhich\s*website\b",
        r"\bwhere\s*to\s*apply\b",
        r"\bwhere\s*to\s*check\b",
        r"\blink\b",
        r"\bwebsite\b",
        r"\bwhere\b"
    ],
    "how_to_do": [
        r"\bhow\s*do\s*i\s*do\s*this\b",
        r"\bhow\s*to\s*fill\b",
        r"\bhow\s*to\s*submit\b",
        r"\bhow\s*to\s*check\b",
    ],
    "document_help": [
        r"\bwhat\s*documents?\b",
        r"\bwhat\s*proof\b",
        r"\bwhat\s*id\b",
        r"\bwhat\s*should\s*i\s*carry\b",
    ],
    "step_reference": [
        r"\bexplain\s*step\s*(\d+)\b",
        r"\bstep\s*(\d+)\b",
        r"\btell\s*me\s*(more\s*about\s*)?step\s*(\d+)\b",
    ]
}

_FOLLOWUP_RE = {
    intent: [re.compile(p, re.IGNORECASE) for p in patterns]
    for intent, patterns in _FOLLOWUP_INTENTS.items()
}

def detect_followup_intent(message: str) -> Optional[str]:
    msg_lower = message.lower().strip()
    
    # Check exact step match first
    for pattern in _FOLLOWUP_RE["step_reference"]:
        match = pattern.search(msg_lower)
        if match:
            return f"step_reference_{match.group(1)}"

    for intent, patterns in _FOLLOWUP_RE.items():
        if intent == "step_reference": continue
        if any(p.search(msg_lower) for p in patterns):
            return intent
            
    # Also catch simple unclear_followups mapped to continue_next or explain_current
    if msg_lower in {"yes", "yeah", "yep", "ok", "okay", "go on", "go ahead", "please"}:
        return "continue_next"
        
    return None

def handle_followup(message: str, context: Dict[str, Any], persona: str) -> Optional[Dict[str, Any]]:
    """
    Returns dict with answer and metadata if context handles the followup.
    """
    if not context.get("active"):
        return None
        
    intent = detect_followup_intent(message)
    if not intent:
        return None
        
    last_topic = context.get("last_topic")
    
    logger.info(f"Context Followup | intent={intent} | last_topic={last_topic}")
    
    # Basic logic for continue_next
    if intent == "continue_next":
        if last_topic == "form6":
            answer = (
                "Your next step is to complete Form 6 on voters.eci.gov.in if you are eligible. "
                "Keep your photo, age proof, and address proof ready. "
                "After submitting, you can track your application, and then check your name in the voter list.\n\n"
                "Do you want help with the documents needed, or tracking your application?"
            )
            if persona == "first-time-voter":
                answer = "Great! " + answer
            elif persona == "elderly":
                answer = "The next step is to fill Form 6. You can do this online at voters.eci.gov.in. Keep your ID proofs ready. Would you like me to tell you which documents are needed?"
            
            return {
                "answer": answer,
                "followup_intent": intent,
                "last_topic": "form6",
                "suggested_replies": ["What documents do I need?", "Track my application", "How do I check my name?"]
            }
            
        elif last_topic == "eligibility":
            return {
                "answer": "If you are eligible, your next step is to fill Form 6 to register as a voter. Do you want me to explain Form 6?",
                "followup_intent": intent,
                "last_topic": "eligibility",
                "suggested_replies": ["What is Form 6?", "What documents are needed?"]
            }
            
        elif last_topic == "voter_list":
            return {
                "answer": "Once you confirm your name is in the voter list, the next step is to find your assigned polling booth. Would you like to know how?",
                "followup_intent": intent,
                "last_topic": "voter_list",
                "suggested_replies": ["Find polling booth", "What ID do I carry?", "Explain polling day"]
            }
            
        elif last_topic == "accepted_id":
            return {
                "answer": "Once you have your accepted ID ready, your next step is to go to your assigned polling booth on election day and cast your vote. Do you want me to explain what happens on polling day?",
                "followup_intent": intent,
                "last_topic": "accepted_id",
                "suggested_replies": ["Find polling booth", "Explain polling day", "What is VVPAT?", "Check my name"]
            }
            
        elif last_topic == "polling_booth":
            return {
                "answer": "Once you know your booth, the next step is to carry your accepted ID to the booth on polling day and vote. Would you like to know what happens inside the booth?",
                "followup_intent": intent,
                "last_topic": "polling_booth",
                "suggested_replies": ["Explain polling day", "What ID do I carry?", "What is VVPAT?"]
            }
            
        else:
            return {
                "answer": "Sure — do you want the next step for voter registration, checking your name, finding your booth, or polling day?",
                "followup_intent": intent,
                "last_topic": last_topic,
                "suggested_replies": ["Voter registration", "Checking my name", "Finding my booth", "Polling day"]
            }
            
    elif intent == "document_help" and last_topic in ["form6", "eligibility", "turning_18_soon"]:
        return {
            "answer": "To register as a voter, you generally need a passport-size photograph, an age proof (like birth certificate or mark sheet), and an address proof (like Aadhaar, utility bill, or passport).",
            "followup_intent": intent,
            "last_topic": "form6",
            "suggested_replies": ["What should I do next?", "Where do I apply?"]
        }
        
    elif intent == "where_to_do":
        return {
            "answer": "You can access official voter services like registration and searching the voter list on the official Voters' Services Portal: voters.eci.gov.in.",
            "followup_intent": intent,
            "last_topic": last_topic,
            "suggested_replies": ["What should I do next?", "Explain more"]
        }

    # Step reference handler
    if intent.startswith("step_reference_"):
        step_idx = int(intent.split("_")[-1]) - 1
        steps = context.get("last_path_steps", [])
        if 0 <= step_idx < len(steps):
            step_id = steps[step_idx].get("id")
            
            intent_map = {
                "check_eligibility": "eligibility",
                "upload_docs": "form6",
                "track_app": "form6",
                "verify_details": "voter_list",
                "check_name": "voter_list",
                "register_form6": "form6",
                "find_booth": "polling_booth",
                "carry_id": "accepted_id",
                "vote": "polling_day"
            }
            mapped_topic = intent_map.get(step_id, step_id)
            
            # Use basic explanations for the requested step
            answer = f"Step {step_idx + 1} is {steps[step_idx].get('title')}. "
            if mapped_topic == "form6":
                answer += "This involves filling out Form 6 online at voters.eci.gov.in with your details."
            elif mapped_topic == "voter_list":
                answer += "This means checking the electoral roll on voters.eci.gov.in to confirm your name is registered."
            elif mapped_topic == "polling_booth":
                answer += "You can find your assigned polling station by checking your voter details on voters.eci.gov.in."
            
            return {
                "answer": answer,
                "followup_intent": intent,
                "last_topic": mapped_topic,
                "suggested_replies": ["What after that?", "Explain more"]
            }

    # If it's a generic explain_current and we have a topic, we can just say we are explaining it
    if intent == "explain_current" and last_topic:
        if last_topic == "form6":
            answer = "Form 6 is the application form for new voters. You fill it out online to get your name on the voter list and get a Voter ID card."
        elif last_topic == "voter_list":
            answer = "The voter list (electoral roll) is the official list of people who are allowed to vote in a specific area."
        else:
            answer = "This relates to your voter journey. You can check the details on the official ECI portal."
            
        return {
            "answer": answer,
            "followup_intent": intent,
            "last_topic": last_topic,
            "suggested_replies": ["What should I do next?", "Where do I do this?"]
        }

    return None

def update_context_from_guided_flow(result: dict) -> dict:
    """Updates context using state from guided flow."""
    state = result.get("guided_flow_state", {})
    step = result.get("guided_flow_step")
    
    context = {
        "active": True,
        "flow_type": state.get("flow_type"),
        "last_topic": None,
        "last_action": step,
        "last_path_steps": state.get("last_path_steps", []),
        "current_step_index": None,
        "awaiting_user_choice": False
    }
    
    if step == "followup_form6":
        context["last_topic"] = "form6"
    elif step == "followup_eligibility":
        context["last_topic"] = "eligibility"
    elif step == "followup_voter_list":
        context["last_topic"] = "voter_list"
    elif step == "followup_accepted_id":
        context["last_topic"] = "accepted_id"
    elif step == "followup_booth":
        context["last_topic"] = "polling_booth"
    elif step == "followup_polling_day":
        context["last_topic"] = "polling_day"
    elif step == "followup_evm":
        context["last_topic"] = "evm_vvpat"
    elif step in ["show_path_no_epic", "show_path_has_epic", "show_path_turning_18", "show_returning_voter"]:
        # User was shown the path. Next logical step is usually they ask for step 1
        if state.get("flow_type") == "first_time_voter_no_epic":
            context["last_topic"] = "eligibility"
        else:
            context["last_topic"] = "voter_list"
        
    return context
