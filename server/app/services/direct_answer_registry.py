"""
Direct Answer Registry
Maps specific exact intents to high-quality, verified answers.
Prevents RAG hallucination on precise definitional questions.
"""
from typing import Optional

_DIRECT_ANSWERS = {
    "what_is_voting": "Voting is the process by which citizens choose their representatives for the government. It is a fundamental democratic right in India.",
    "what_is_candidate": "A candidate is a person who contests an election to be elected as a representative. They can belong to a political party or run as an independent.",
    "what_is_constituency": "A constituency is a specific geographical area whose registered voters elect a representative to a legislative body like the Lok Sabha or Vidhan Sabha.",
    "what_is_opposition": "The opposition refers to the political parties in a legislature that do not form the government. Their role is to question the government and hold it accountable.",
    "what_is_parliament": "Parliament is India's supreme legislative body. It consists of the President, the Lok Sabha (House of the People), and the Rajya Sabha (Council of States).",
    "what_is_lok_sabha": "The Lok Sabha, or House of the People, is the lower house of India's Parliament. Members are directly elected by the public.",
    "what_is_vidhan_sabha": "The Vidhan Sabha, or Legislative Assembly, is the lower house of a state's legislature in India. Members are directly elected by the public of that state.",
    "how_to_use_evm": "To use an EVM, press the blue button next to the candidate of your choice. A red light will glow and a beep sound will confirm your vote.",
    "what_is_vvpat": "VVPAT (Voter Verifiable Paper Audit Trail) is a machine attached to the EVM. It prints a slip with your candidate's name and symbol, visible for 7 seconds behind glass, allowing you to verify your vote.",
    "what_id_to_carry": "On polling day, you must carry your Voter ID (EPIC). If you don't have it, you can use one of the 12 approved photo IDs like Aadhaar, PAN card, or Passport.",
    "can_i_use_aadhaar": "Yes, Aadhaar card is one of the 12 approved alternative photo IDs you can use to vote if you don't have your Voter ID card.",
    "forgot_voter_id": "If you forgot your Voter ID, you can still vote by showing one of the 12 alternative approved photo IDs (like Aadhaar, PAN card, Passport, or Driving License).",
    "polling_staff_influence": "No polling staff or officer can tell you who to vote for. Your vote is your independent choice.",
    "vote_secrecy": "Yes, your vote is completely secret. The EVM does not record your name with your vote, and the voting compartment ensures privacy.",
    "evm_wrong_button": "Once you press a button on the EVM and the beep sounds, your vote is cast and cannot be changed. Take your time to press the correct button.",
    "vote_twice": "No, it is illegal to vote more than once. When you vote, indelible ink is applied to your finger to prevent double voting.",
    "double_voter_list": "If your name is in two voter lists, it is illegal. You must apply for deletion (Form 7) from one place immediately.",
    "double_voting": "Voting from two places or voting twice is a punishable offense under the Representation of the People Act.",
    "fake_voter_id": "Using a fake Voter ID or impersonating someone else to vote is a criminal offense under Indian law.",
    "who_can_fill_form_6": "Form 6 can be filled by any Indian citizen who is 18 years or older on the qualifying date and wants to register as a new voter.",
    "online_registration": "Yes, you can register to vote online by visiting voters.eci.gov.in and filling out Form 6."
}

def get_direct_answer(intent: str) -> Optional[str]:
    """Returns a verified exact answer for a given intent, or None if not found."""
    return _DIRECT_ANSWERS.get(intent)
