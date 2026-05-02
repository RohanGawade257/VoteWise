import asyncio
import httpx
import json

FAILED_QUESTIONS = [
    "What is voting?",
    "What is a candidate?",
    "What is a constituency?",
    "What is opposition?",
    "What is Parliament?",
    "What is Lok Sabha?",
    "What is Vidhan Sabha?",
    "How do I use EVM?",
    "What is VVPAT?",
    "What ID do I carry on voting day?",
    "Can I use Aadhaar card to vote?",
    "What if I forgot my voter ID?",
    "Can polling staff tell me who to vote for?",
    "Is my vote secret?",
    "What if I press the wrong button on EVM?",
    "Can I vote twice?",
    "What if my name is in two voter lists?",
    "Can I vote from two places?",
    "What happens if someone uses fake voter ID?",
    "Who can fill Form 6?",
    "Can I register online?",
]

async def test_questions():
    async with httpx.AsyncClient(timeout=30.0) as client:
        for q in FAILED_QUESTIONS:
            payload = {
                "message": q,
                "persona": "general",
                "guidedFlow": {"active": False, "step": None, "state": {}}
            }
            try:
                response = await client.post("http://127.0.0.1:8080/api/chat", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    intent = data.get("meta", {}).get("intent", "UNKNOWN")
                    # Check if answer is generic first-time voter guide
                    is_generic = "visit voters.eci.gov.in" in answer.lower() and "form 6" in answer.lower() and "registration" in answer.lower()
                    print(f"Q: {q}")
                    print(f"Intent: {intent}")
                    print(f"Generic Guide Detected: {is_generic}")
                    print(f"Answer: {answer[:100]}...\n")
                else:
                    print(f"Failed Q: {q} with status {response.status_code}\n")
            except Exception as e:
                print(f"Exception on Q: {q} -> {e}\n")

if __name__ == "__main__":
    asyncio.run(test_questions())
