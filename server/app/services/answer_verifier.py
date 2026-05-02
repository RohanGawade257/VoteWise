"""
Answer Verifier Service
Verifies that the generated response aligns with the classified intent.
Prevents generic fallback guides from being returned for specific definitional questions.
"""

def verify_answer(answer: str, intent_type: str, specific_intent: str) -> bool:
    """
    Returns True if the answer appears to be a valid response for the intent type.
    Returns False if the answer seems to be a generic hallucinated guide instead of addressing the intent.
    """
    answer_lower = answer.lower()
    
    # If the intent was a definition, the answer should be relatively concise and explanatory.
    if intent_type == "definition":
        # A hallucinated First-Time Voter Guide usually contains many steps or mentions "Form 6", "register online", etc.
        # when it shouldn't for a simple definition.
        if "step-by-step registration" in answer_lower or "visit voters.eci.gov.in" in answer_lower and "form 6" in answer_lower:
            # It's highly likely this is the First-Time Voter guide hijacking the response.
            # But wait, what if the definition is "Form 6"? We need to be careful.
            if specific_intent != "what_is_form_6" and specific_intent != "who_can_fill_form_6":
                return False
                
    # If the intent is yes_no, the answer should ideally contain yes or no.
    if intent_type == "yes_no":
        if "yes" not in answer_lower and "no" not in answer_lower and "cannot" not in answer_lower and "can" not in answer_lower:
            return False

    return True
