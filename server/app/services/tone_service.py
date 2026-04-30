"""
Tone Service — Centralized manager for persona-aware text generation and formatting.
Ensures consistency across guided flow, safety refusals, out-of-scope replies, and Gemini prompts.
"""

# ---------------------------------------------------------------------------
# Persona normalization
# ---------------------------------------------------------------------------
_PERSONA_ALIASES: dict[str, str] = {
    "school-student":   "student",
    "school_student":   "student",
    "schoolstudent":    "student",
    "first_time_voter": "first-time-voter",
    "firsttimevoter":   "first-time-voter",
    "first time voter": "first-time-voter",
}
_VALID_PERSONAS: frozenset[str] = frozenset({"general", "first-time-voter", "student", "elderly"})

def normalize_persona(raw: "str | None") -> str:
    if not raw:
        return "general"
    p = raw.strip().lower()
    normalised = _PERSONA_ALIASES.get(p, p)
    return normalised if normalised in _VALID_PERSONAS else "general"


# ---------------------------------------------------------------------------
# Tone Rules (For Gemini Prompts)
# ---------------------------------------------------------------------------
def get_tone_rules(persona: str) -> dict:
    """Returns Gemini prompt instructions and formatting rules for a given persona."""
    rules = {
        "general": {
            "instruction": "TONE — General adult citizen. Be clear, neutral, and concise. Assume moderate civic awareness. Avoid over-explaining obvious steps. Use bullet points only when listing multiple items.",
            "format": "Keep answers max 160-180 words. The selected persona must affect wording, pacing, and structure, but not factual content or safety boundaries."
        },
        "first-time-voter": {
            "instruction": "TONE — First-Time Voter. The user has never voted before and may feel uncertain. Be friendly, encouraging, and step-by-step. Assume the user is new. Explain terms like EPIC or Form 6 briefly. End your answer with 'next step' guidance.",
            "format": "Keep answers max 180 words. Provide step-by-step structure. The selected persona must affect wording, pacing, and structure, but not factual content or safety boundaries."
        },
        "student": {
            "instruction": "TONE — School Student. Use very simple, everyday words. Adopt a patient, teacher-like tone. Use one simple relatable analogy if useful. Avoid all legal/technical jargon. Use short paragraphs. Explain 'why it matters'.",
            "format": "Keep answers max 140-160 words. Short paragraphs, simple language. The selected persona must affect wording, pacing, and structure, but not factual content or safety boundaries."
        },
        "elderly": {
            "instruction": "TONE — Elderly citizen. Calm and respectful tone. Avoid jargon. Provide one step at a time. Avoid giving too many choices at once. Use reassurance but do not use a babyish tone. Always expand abbreviations on first use.",
            "format": "Keep answers max 120-140 words. Very short sentences, one idea per sentence. The selected persona must affect wording, pacing, and structure, but not factual content or safety boundaries."
        }
    }
    return rules.get(persona, rules["general"])


# ---------------------------------------------------------------------------
# Templates (For direct backend responses)
# ---------------------------------------------------------------------------
_TEMPLATES = {
    # -- Guided Flow Questions --
    "ask_first_time": {
        "general": "Are you voting for the first time?",
        "first-time-voter": "Exciting! Is this your first time voting? 🗳️",
        "student": "Is this going to be your very first time voting?",
        "elderly": "Will this be your first time voting?"
    },
    "ask_age_status": {
        "general": "Are you already 18, or will you turn 18 soon?",
        "first-time-voter": "Great! Are you already 18 years old, or will you be turning 18 soon?",
        "student": "Are you 18 yet, or will you turn 18 soon?",
        "elderly": "How old are you? Are you already 18 or turning 18 soon?"
    },
    "ask_has_epic": {
        "general": "Do you already have a Voter ID / EPIC number?",
        "first-time-voter": "Do you already have a Voter ID card or EPIC number? If you are not sure, choose 'Not sure'.",
        "student": "Do you already have a voter card? It is also called EPIC. You can say Yes, No, or Not sure.",
        "elderly": "Do you already have a Voter ID card? It may also be called EPIC. Please choose one option."
    },
    "ask_goal": {
        "general": "What would you like help with today?",
        "first-time-voter": "What can I help you with today? Choose one or just type your question!",
        "student": "What do you want to learn about? Pick one!",
        "elderly": "What do you need help with? Take your time."
    },
    "reask_first_time": {
        "general": "I didn't quite catch that. Are you voting for the first time, or have you voted before?",
        "first-time-voter": "No worries! Just tell me — is this your first time, or have you voted before? 😊",
        "student": "Hmm, could you say that again? Is this your first election or not?",
        "elderly": "Could you please clarify? Is this your first time voting?"
    },
    "reask_age_status": {
        "general": "Please choose: are you already 18, turning 18 soon, or under 18?",
        "first-time-voter": "Just tell me — are you 18 already, turning 18 soon, or younger than 18?",
        "student": "Are you already 18, about to turn 18, or younger than 18?",
        "elderly": "Please let me know: are you 18 or older, turning 18 soon, or younger?"
    },
    "reask_has_epic": {
        "general": "No problem! You can check if you have a Voter ID by searching at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). Would you like me to show you the registration steps just in case?",
        "first-time-voter": "That's okay! You can check your Voter ID status at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). Shall I walk you through registering from scratch?",
        "student": "You can find out at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). Want me to show the registration steps?",
        "elderly": "You can check at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). Shall I explain how to register?"
    },
    
    # -- Guided Flow Terminal Paths --
    "show_path_no_epic": {
        "general": "**Your First-Time Voter Path**\n\nSince you are 18+ and don't have a Voter ID yet, here are your steps:\n\n- **Step 1 — Check eligibility:** Must be 18+, Indian citizen, and resident of your constituency\n- **Step 2 — Register online:** Go to [voters.eci.gov.in](https://voters.eci.gov.in) and fill **Form 6**\n- **Step 3 — Upload documents:** Passport photo, age proof, address proof\n- **Step 4 — Track your application:** Use your reference number on the portal\n- **Step 5 — Check your name in the voter list:** Verify at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n- **Step 6 — Find your polling booth:** Check on [voters.eci.gov.in](https://voters.eci.gov.in)\n- **Step 7 — Vote on polling day:** Carry an accepted ID and use the EVM\n\n> All registration must be done on [voters.eci.gov.in](https://voters.eci.gov.in).\n\nWhich step would you like me to explain?",
        "first-time-voter": "**You're on your way! 🎉 Here's your personalised voter journey:**\n\n- ✅ **Step 1 — Check eligibility:** 18+, Indian citizen\n- ✅ **Step 2 — Register with Form 6:** Visit [voters.eci.gov.in](https://voters.eci.gov.in)\n- ✅ **Step 3 — Upload documents:** Photo, age proof, address proof\n- ✅ **Step 4 — Track your application**\n- ✅ **Step 5 — Verify your name** in the voter list\n- ✅ **Step 6 — Find your booth** on the portal\n- ✅ **Step 7 — Vote on polling day!** Bring your ID\n\n> Remember: VoteWise can guide you, but the real registration happens at [voters.eci.gov.in](https://voters.eci.gov.in) 🏛️\n\nYour next best step is to check if you are eligible. Which step would you like me to explain?",
        "student": "**Here are your steps to vote for the first time:**\n\nJust like getting a library card, you need to register first!\n\n1. Make sure you are 18 and an Indian citizen.\n2. Register using Form 6 on [voters.eci.gov.in](https://voters.eci.gov.in).\n3. Upload your photo, age proof, and address proof.\n4. Track your application.\n5. Check your name in the voter list.\n6. Find your polling booth.\n7. Vote on the polling day!\n\nThis matters because you need to be on the official list to vote. Which one do you want me to explain?",
        "elderly": "Here is what you need to do, one step at a time:\n\nStep 1: Check you are 18 and an Indian citizen.\nStep 2: Go to [voters.eci.gov.in](https://voters.eci.gov.in) to fill Form 6.\nStep 3: Keep your photo, age proof, and address proof ready.\n\nWe can go over the other steps later. Which of these three steps would you like explained first?"
    },
    "show_path_has_epic": {
        "general": "**Great — you already have a Voter ID! Here's what to do next:**\n\n- **Step 1 — Verify your name** in the Electoral Roll at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n- **Step 2 — Check your details** — name, photo, constituency, and booth number\n- **Step 3 — Find your polling booth** on [voters.eci.gov.in](https://voters.eci.gov.in)\n- **Step 4 — Carry accepted ID on polling day** — your Voter ID, Aadhaar, PAN, or Passport\n- **Step 5 — Vote using the EVM** — the VVPAT slip confirms your vote\n\nWhich step would you like me to explain?",
        "first-time-voter": "**You're almost ready to vote! 🗳️ Just a few things to check:**\n\n- ✅ **Check your name** at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n- ✅ **Find your booth** on [voters.eci.gov.in](https://voters.eci.gov.in)\n- ✅ **Carry a valid ID** on polling day (Voter ID, Aadhaar, PAN, or Passport)\n- ✅ **Vote using the EVM**\n\nYour next best step is to check your name on the list. Which step would you like to know more about?",
        "student": "**You already have a Voter ID — here's your checklist:**\n\nThink of your Voter ID like a school ID, but for voting! Now you just need to:\n\n1. Check your name is in the voter list.\n2. Find your polling booth.\n3. On polling day, carry your ID and go vote!\n\nThis matters so you know exactly where to go on election day. What would you like to know more about?",
        "elderly": "Good, you have a Voter ID.\n\nStep 1: Check your name in the voter list at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in).\nStep 2: Find your polling booth.\nStep 3: On polling day, carry your Voter ID or any accepted ID and vote.\n\nWhich step would you like explained?"
    },
    "show_path_turning_18": {
        "general": "**You're eligible to register even before you turn 18! Here's what to know:**\n\n- Form 6 is for new voter registration and is open to citizens who are **18 or turning 18** on or before the qualifying date.\n- Register in advance at [voters.eci.gov.in](https://voters.eci.gov.in)\n- Prepare your documents: age proof, address proof, and a photo\n- **Always verify the current eligibility date and deadline** at [eci.gov.in](https://eci.gov.in)\n\n> VoteWise cannot confirm your exact eligibility date. Please verify on the official portal.",
        "first-time-voter": "**So exciting that you'll be voting soon! 🌟**\n\nHere's the good news: you can register **before** you actually turn 18, as long as you'll be 18 by the qualifying date.\n\n- Visit [voters.eci.gov.in](https://voters.eci.gov.in) and fill Form 6\n- Keep your age proof ready\n- Check back on the portal to confirm your registration\n\nYour next best step is to check the exact qualifying date at [eci.gov.in](https://eci.gov.in).",
        "student": "**Good news — you can register before you turn 18!**\n\nIt's like getting early admission! If you'll be 18 by the qualifying date, you can fill Form 6 now on [voters.eci.gov.in](https://voters.eci.gov.in).\n\nKeep your birth certificate or 10th mark sheet ready as age proof. This matters so you don't miss out on voting in the next election!\n\nCheck [eci.gov.in](https://eci.gov.in) for the exact date rules.",
        "elderly": "You can register soon.\n\nVisit [voters.eci.gov.in](https://voters.eci.gov.in) and fill Form 6 when you are ready.\n\nKeep your age proof (birth certificate) and address proof ready.\n\nFor exact dates, check [eci.gov.in](https://eci.gov.in)."
    },
    "show_under_18": {
        "general": "You cannot vote yet — the minimum voting age in India is **18 years**.\n\nBut that doesn't mean you can't learn! VoteWise can teach you:\n- How elections work\n- What parties and candidates do\n- How EVMs and VVPAT work\n- What the election timeline looks like\n\nWhat would you like to learn about?",
        "first-time-voter": "You can't vote just yet — India's voting age is **18** — but you're already thinking ahead, which is great! 🌟\n\nI can help you learn everything about elections so you're fully ready when the time comes.\n\nWhat topic interests you?",
        "student": "You need to be 18 to vote in India. Just like you need to be 18 to get a driving licence! But you can still learn.\n\nI can explain how elections work, what parties do, what EVM is, and much more. Learning this now matters because you'll be a smart voter later!\n\nWhat would you like to learn about?",
        "elderly": "The voting age in India is 18. You cannot vote yet.\n\nBut I can still teach you how elections work. What would you like to know?"
    },
    "show_returning_voter": {
        "general": "Welcome back! Since you've voted before, here's a quick refresher:\n\n- **Check your name** in the current Electoral Roll at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n- **Find your booth** on [voters.eci.gov.in](https://voters.eci.gov.in)\n- **Carry valid ID** — Voter ID, Aadhaar, PAN, or Passport\n\nIs there something specific I can help with?",
        "first-time-voter": "Great to hear you've voted before! 🗳️\n\nJust make sure your name is still in the voter list and your booth is the same.\n\nYour next best step is to check your name at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). Is there something specific you want help with?",
        "student": "Good, you've voted before! It's like re-registering for the next school year. Here's what to check:\n1. Is your name still in the voter list?\n2. Has your polling booth changed?\n3. Do you have a valid ID?\n\nChecking this matters so you don't face surprises on polling day. What do you need help with?",
        "elderly": "Good. Since you have voted before, just check your name in the voter list and find your booth.\n\nWhat would you like help with?"
    },

    # -- Contextual Follow-up Tone --
    "followup_accepted_id": {
        "general": "First, make sure your name is in the voter list. Carry your EPIC/Voter ID if you have it. If not, ECI allows alternative photo ID documents. Common examples include Aadhaar Card, PAN Card, Driving Licence, Passport, and MGNREGA Job Card.\n\nThe accepted list can change for a specific election, so verify from [eci.gov.in](https://eci.gov.in) before polling day.",
        "first-time-voter": "Good question. On polling day, two things matter: your name should be in the voter list, and you should carry an accepted photo ID. If you have your Voter ID (EPIC), bring it! Otherwise, you can bring an Aadhaar Card, PAN Card, Passport, or Driving Licence. Check [eci.gov.in](https://eci.gov.in) to be sure.",
        "student": "Think of voting like entering an exam hall. Your name must be on the list, and you must carry an ID to prove who you are. The best ID is your Voter ID card. If you don't have it, Aadhaar or PAN card works too! This matters so nobody else can vote in your place.",
        "elderly": "Please check two things. First, your name should be in the voter list. Second, carry a photo ID. If you have Voter ID, carry it. If not, you can carry your Aadhaar card or PAN card."
    },
    "followup_voter_list": {
        "general": "You can check your name in the electoral roll by visiting [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). You can search by your EPIC number, personal details, or mobile number.",
        "first-time-voter": "It's super easy to check! Just go to [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in) and enter your EPIC number, or search using your name and state.",
        "student": "You can easily check if your name is on the list by going to [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). Just like checking exam results online!",
        "elderly": "Please visit [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in) to check your name. You can search using your Voter ID number."
    },
    "followup_form6": {
        "general": "**Form 6** is the official application form for new voters to register in the electoral roll. Fill it online at [voters.eci.gov.in](https://voters.eci.gov.in). You will need a photograph, age proof, and address proof.",
        "first-time-voter": "**Form 6** is what you fill out to become a registered voter! You can do it all online at [voters.eci.gov.in](https://voters.eci.gov.in). Just upload your photo, age proof, and address proof.",
        "student": "**Form 6** is the official form you fill out to tell the government you want to be a voter. It's like filling an admission form! You can do it online at [voters.eci.gov.in](https://voters.eci.gov.in).",
        "elderly": "Form 6 is the form you use to register as a new voter. You can fill it out on the website [voters.eci.gov.in](https://voters.eci.gov.in)."
    },
    "followup_epic": {
        "general": "EPIC stands for Electors Photo Identity Card, commonly known as your Voter ID card. It contains your photograph, name, address, and EPIC number. Remember, having an EPIC is not enough — your name must also be in the current voter list.",
        "first-time-voter": "EPIC is just the official name for your Voter ID card! It proves you are a registered voter. But remember, even with an EPIC, you must check that your name is on the current voter list.",
        "student": "EPIC stands for Electors Photo Identity Card. It's simply your Voter ID card! It's like your school ID but for elections. You show it at the booth to prove who you are.",
        "elderly": "EPIC is your Voter ID card. It has your photo and a unique number. Please remember that you must also check if your name is on the voter list."
    },
    "followup_booth": {
        "general": "Your polling booth is the specific location where you go to cast your vote. You can find your exact polling booth details by searching your name at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in) or calling **1950**.",
        "first-time-voter": "Your polling booth is the room where you actually go to vote! You can find out exactly where yours is by searching your name at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in).",
        "student": "Your polling booth is the specific school or building where you go to cast your vote. It's like your assigned classroom for an exam. You can find it at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in).",
        "elderly": "Your polling booth is the place where you go to vote. You can find the address by searching your name at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in) or calling 1950."
    },
    "followup_polling_day": {
        "general": "On polling day, you go to your assigned polling booth. First, a polling officer checks your name and ID. Then, your finger is marked with indelible ink. Finally, you go to the voting compartment, press the button next to your chosen candidate on the EVM, and a VVPAT slip prints to confirm your vote.",
        "first-time-voter": "On polling day, you'll go to your booth. The officer will check your ID and mark your finger with ink. Then you'll go to the voting machine (EVM), press the button for your candidate, and a paper slip (VVPAT) will show your vote was recorded! Your next best step is just to be prepared with your ID.",
        "student": "On polling day, you go to your booth. An officer checks your ID. Then they put a special ink mark on your finger so you can't vote twice. You press a button on the voting machine (EVM) to choose your candidate. It's as simple as pressing a button on a vending machine!",
        "elderly": "On polling day, go to your booth with your ID. The officer will check your name. They will put a small ink mark on your finger. Then you go to the voting machine and press the button for your candidate."
    },
    "followup_evm": {
        "general": "**EVM** (Electronic Voting Machine) is where you press a button to cast your vote. **VVPAT** (Voter Verifiable Paper Audit Trail) is a printer attached to the EVM. When you vote, it prints a paper slip showing your choice, visible for 7 seconds behind glass, then drops into a sealed box.",
        "first-time-voter": "The **EVM** is the machine with buttons where you cast your vote. The **VVPAT** is a printer next to it. After you press the button, the VVPAT prints a little slip with your candidate's symbol so you can be 100% sure your vote went to the right person!",
        "student": "The **EVM** is the machine where you press a button to vote. The **VVPAT** is like a receipt printer attached to it. It prints a slip showing who you voted for, so you can see your vote was counted correctly! It matters because it makes elections fair and clear.",
        "elderly": "The EVM is the electronic machine where you vote. You just press the blue button next to your candidate's symbol. The VVPAT is a printer. It will print a slip showing your vote so you can check it."
    },
    "followup_eligibility": {
        "general": "To be eligible to vote in India, you must be a citizen of India, at least 18 years old on the qualifying date (usually January 1 of the year), and a resident of the polling area. You must not be disqualified due to corrupt practices or other legal reasons.",
        "first-time-voter": "To vote, you just need to be an Indian citizen and 18 years old by the qualifying date! You also need to live in the area where you want to vote.",
        "student": "To be eligible, you need to be an Indian citizen and 18 years old. It's like the age limit for getting a driving licence! You also must live in the area you are voting in.",
        "elderly": "You are eligible to vote if you are an Indian citizen, 18 years of age, and a resident of the area."
    },
    "followup_docs": {
        "general": "When registering to vote via Form 6, you generally need to upload: 1) A recent passport-sized photograph. 2) Proof of Age (birth certificate, 10th mark sheet, Aadhaar, PAN). 3) Proof of Address (Aadhaar, electricity bill, passport, or bank passbook).",
        "first-time-voter": "When you fill out Form 6, keep a nice passport photo ready! You'll also need a document showing your age (like your 10th mark sheet or Aadhaar) and a document showing where you live (like Aadhaar or a recent electricity bill).",
        "student": "You need a passport photo, something that shows how old you are (like an Aadhaar or birth certificate), and something that shows where you live. Just like when you take admission in a new school!",
        "elderly": "Please keep a passport photo, age proof, and address proof ready for your application."
    },
    "followup_tracking": {
        "general": "After submitting Form 6, you will receive a reference number. You can use this reference number on [voters.eci.gov.in](https://voters.eci.gov.in) to track the status of your application. Once approved, your name will be added to the electoral roll.",
        "first-time-voter": "After you submit Form 6, you get a reference number. It's like a tracking number for an online order! Use it on [voters.eci.gov.in](https://voters.eci.gov.in) to see when your name gets added to the voter list.",
        "student": "Once you submit Form 6, you get a tracking number. Just like tracking a package delivery online, you can track your voter application at [voters.eci.gov.in](https://voters.eci.gov.in)!",
        "elderly": "After submitting the form, you get a reference number. You can use this number on the website to check if your application is approved."
    },
    "fallback_first_time_voter": {
        "general": "**First-Time Voter Guide**\n\nHere is what you need to do to vote for the first time in India:\n\n- **Check eligibility** — Must be 18+, an Indian citizen, and a resident of your constituency\n- **Register online** — Visit [voters.eci.gov.in](https://voters.eci.gov.in) and fill **Form 6**. Upload a photo, age proof, and address proof\n- **Verify your name** — Check your name in the Electoral Roll at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n- **Find your booth** — Your polling station is assigned after registration. Check it on [voters.eci.gov.in](https://voters.eci.gov.in) or call **1950**\n- **Carry valid ID on polling day** — EPIC (Voter ID), Aadhaar, PAN, Passport, or Driving Licence are accepted\n- **Vote using the EVM** — Press the button next to your candidate. A VVPAT slip will confirm your vote\n\n> For official actions, always verify on [voters.eci.gov.in](https://voters.eci.gov.in) or [eci.gov.in](https://eci.gov.in).",
        "first-time-voter": "**First-Time Voter Guide**\n\nHere is your step-by-step guide to voting for the first time! 🎉\n\n- **Check eligibility** — You need to be 18+ and an Indian citizen\n- **Register online** — Visit [voters.eci.gov.in](https://voters.eci.gov.in) and fill **Form 6** with your photo, age proof, and address proof\n- **Verify your name** — Check the voter list at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n- **Find your booth** — Find your voting booth on the portal\n- **Carry valid ID on polling day** — Bring your Voter ID, Aadhaar, PAN, or Passport\n- **Vote using the EVM** — Press the button and see the VVPAT slip confirm your vote!\n\n> Remember: Always use [voters.eci.gov.in](https://voters.eci.gov.in) for official registration.",
        "student": "**How to Vote (A Simple Guide)**\n\nVoting in India is like a big national exam, but much easier! Here are the steps:\n\n- **Step 1: Check eligibility** — Just like turning 18 to get a driving licence, you need to be 18+ to vote\n- **Step 2: Register** — Fill out **Form 6** on [voters.eci.gov.in](https://voters.eci.gov.in) (it's like an admission form)\n- **Step 3: Check the list** — Make sure your name is on the final voter list at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n- **Step 4: Go to the booth** — Your assigned polling booth is where you go on election day\n- **Step 5: Vote!** — Show your ID (like Aadhaar or Voter ID) and press the button on the EVM.\n\n> For official info, always check [eci.gov.in](https://eci.gov.in).",
        "elderly": "**Guide for New Voters**\n\nHere are the simple steps to vote:\n\n1. **Check eligibility**: Be 18 years old and an Indian citizen.\n2. **Register**: Go to [voters.eci.gov.in](https://voters.eci.gov.in) and fill Form 6.\n3. **Check your name**: Verify it at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in).\n4. **Find your booth**: Check the website or call 1950 to find where to vote.\n5. **Vote**: Carry your Voter ID or Aadhaar on polling day and use the voting machine.\n\n> For official details, please visit [eci.gov.in](https://eci.gov.in)."
    },
    "fallback_evm_vvpat": {
        "general": "**EVM and VVPAT — Explained Simply**\n\n- **EVM (Electronic Voting Machine)** — A tamper-proof device used in Indian elections instead of paper ballots. You press a blue button next to your chosen candidate's name and symbol\n- **VVPAT (Voter Verifiable Paper Audit Trail)** — A machine attached to the EVM that prints a paper slip showing your voted candidate's name and symbol. The slip is visible through a glass window for **7 seconds** before it drops into a sealed box\n- Both machines are manufactured by government PSUs (BEL and ECIL) and are rigorously tested before each election\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "first-time-voter": "**EVM and VVPAT — Explained**\n\n- **EVM** — This is the voting machine! You just press the blue button next to your candidate.\n- **VVPAT** — This is the printer next to the EVM. When you vote, it prints a slip so you can see your choice for 7 seconds. It's the ultimate proof that your vote went to the right person!\n- They are highly secure and tested rigorously before every election.\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "student": "**What are EVM and VVPAT?**\n\n- **EVM** is like a specialized calculator that securely counts votes instead of using paper.\n- **VVPAT** is like a receipt printer. When you press the EVM button, the VVPAT prints a 'receipt' showing your vote for 7 seconds behind a glass window.\n- This double-checks the system and ensures every vote is fair and accurate.\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "elderly": "**About the EVM and VVPAT**\n\n- **EVM**: The electronic machine where you cast your vote by pressing a button.\n- **VVPAT**: A printer attached to the EVM. It prints a slip showing who you voted for. You can see it for 7 seconds to check your vote.\n- These machines are safe and tested.\n\n> Source: [eci.gov.in](https://eci.gov.in)"
    },
    "fallback_nota": {
        "general": "**NOTA — None of the Above**\n\n- **NOTA** stands for **None of the Above**\n- It was introduced in Indian elections from **2013** onwards following a Supreme Court order\n- You can press NOTA on the EVM if you do not wish to vote for any of the listed candidates\n- NOTA votes **are counted** and reported, but they do not cause a re-election. The candidate with the most votes still wins\n- NOTA is a way to formally register dissatisfaction with all candidates\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "first-time-voter": "**What is NOTA?**\n\n- **NOTA** means **None of the Above**.\n- You press it if you don't want to vote for any candidate on the list.\n- NOTA votes are counted! But remember, even if NOTA gets the most votes, the actual candidate with the highest votes still wins. It's a powerful way to register your protest.\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "student": "**Understanding NOTA**\n\n- **NOTA** stands for **None of the Above**.\n- Think of it like a 'skip' button on a test. If you don't like any candidate, you can press NOTA.\n- The votes are counted to show how many people were unhappy with the choices, but the candidate with the highest votes still wins the election.\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "elderly": "**What is NOTA?**\n\n- **NOTA** means **None of the Above**.\n- If you do not like any candidate, you can press the NOTA button on the machine.\n- Your NOTA vote is counted, but the candidate who gets the most actual votes will still win.\n\n> Source: [eci.gov.in](https://eci.gov.in)"
    },
    "fallback_coalition": {
        "general": "**Coalition Government — Explained**\n\n- A **coalition government** is formed when no single political party wins an outright majority (more than 50% of seats) in Parliament\n- Multiple parties with compatible goals join together and agree to share power\n- The **largest party** in the coalition typically provides the Prime Minister\n- A coalition must prove its majority through a **confidence vote** in the Lok Sabha\n- India has had several coalition governments, particularly since the 1990s\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "first-time-voter": "**What is a Coalition Government?**\n\n- Sometimes, no single party wins enough seats (more than 50%) to form a government alone.\n- When this happens, different parties join hands to form a **coalition government**.\n- They share power, and the leader of the biggest party usually becomes the Prime Minister. They must prove they have the majority support in the Lok Sabha.\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "student": "**Coalition Governments Explained**\n\n- To form a government, a party needs more than 50% of the seats, like getting a passing grade.\n- If no party gets 50%, a few parties can team up to combine their seats. This team is called a **coalition**.\n- The coalition works together to run the country, and they must prove their combined strength in Parliament.\n\n> Source: [eci.gov.in](https://eci.gov.in)",
        "elderly": "**About Coalition Governments**\n\n- A **coalition government** is formed when no single party gets a majority of seats.\n- Several parties come together to form the government.\n- The largest party in this group usually leads, and they must prove their majority in Parliament.\n\n> Source: [eci.gov.in](https://eci.gov.in)"
    },
    "fallback_live_schedule": {
        "general": "**Election Dates & Schedule**\n\nElection dates and schedules change with every election cycle and cannot be reliably answered from a static knowledge base.\n\n**Please verify the latest information directly from:**\n- [eci.gov.in](https://eci.gov.in) — Official Election Commission of India\n- [results.eci.gov.in](https://results.eci.gov.in) — Live results\n- Official ECI press releases and notifications",
        "first-time-voter": "**Election Dates & Schedule**\n\nSince election dates change often, I want to make sure you get the most accurate and up-to-date information.\n\n**Please check the official websites:**\n- [eci.gov.in](https://eci.gov.in) — Official Election Commission of India\n- [results.eci.gov.in](https://results.eci.gov.in) — Live results",
        "student": "**Election Dates & Schedule**\n\nElection dates are like live event schedules—they change frequently! For the most accurate and safe information, please check the official source.\n\n**Verify the latest info here:**\n- [eci.gov.in](https://eci.gov.in) — Official Election Commission of India\n- [results.eci.gov.in](https://results.eci.gov.in) — Live results",
        "elderly": "**Election Dates & Schedule**\n\nElection dates change with each election. Please check the official government website for the correct dates.\n\n**Official websites:**\n- [eci.gov.in](https://eci.gov.in) — Official Election Commission of India\n- [results.eci.gov.in](https://results.eci.gov.in) — Live results"
    },
    "fallback_no_chunks": {
        "general": "I wasn't able to find a confident answer in the VoteWise knowledge base for that question.\n\n**Please visit the official sources below for accurate information:**\n- [voters.eci.gov.in](https://voters.eci.gov.in) — Voter registration and status\n- [eci.gov.in](https://eci.gov.in) — Election Commission of India\n- **Voter Helpline:** 1950",
        "first-time-voter": "I couldn't find a confident answer for that in my knowledge base right now.\n\n**For the most accurate information, please check the official sources:**\n- [voters.eci.gov.in](https://voters.eci.gov.in) — Voter registration and status\n- [eci.gov.in](https://eci.gov.in) — Election Commission of India\n- **Voter Helpline:** 1950",
        "student": "I couldn't find the exact answer for that right now.\n\n**To be safe, always check the official rulebook:**\n- [voters.eci.gov.in](https://voters.eci.gov.in) — Voter registration and status\n- [eci.gov.in](https://eci.gov.in) — Election Commission of India\n- **Voter Helpline:** 1950",
        "elderly": "I could not find a clear answer for that right now.\n\n**Please call the helpline or check the official websites:**\n- [voters.eci.gov.in](https://voters.eci.gov.in) — Voter registration and status\n- [eci.gov.in](https://eci.gov.in) — Election Commission of India\n- **Voter Helpline:** 1950"
    },

    # -- Safety / Out-of-scope --
    "safety_political": {
        "general": "I can't tell you who to vote for or promote/attack any party. I can help you compare official manifestos or understand election concepts neutrally. Your vote is private and independent.",
        "first-time-voter": "I can't choose a party for you. Your vote is your private decision. I can help you understand manifestos, party roles, and how to verify information.",
        "student": "I can't say which party is best. That would be unfair. I can explain how voters compare parties using official information. Learning this matters so you can make your own choices!",
        "elderly": "I am sorry, I cannot suggest a party. Your vote is private. I can help you understand the election process and official information."
    },
    "safety_illegal": {
        # Illegal is firm for all
        "general": "I cannot provide guidance on illegal activities such as fake voter IDs, multiple voting, or EVM tampering. For official guidelines, visit eci.gov.in.",
        "first-time-voter": "I cannot provide guidance on illegal activities such as fake voter IDs, multiple voting, or EVM tampering. For official guidelines, visit eci.gov.in.",
        "student": "I cannot provide guidance on illegal activities such as fake voter IDs, multiple voting, or EVM tampering. For official guidelines, visit eci.gov.in.",
        "elderly": "I cannot provide guidance on illegal activities such as fake voter IDs, multiple voting, or EVM tampering. For official guidelines, visit eci.gov.in."
    },
    "out_of_scope": {
        "general": "VoteWise focuses on Indian elections, voter registration, and civic education. I can help with voting steps, EVMs, election timelines, or voter registration. What would you like to know?",
        "first-time-voter": "I'm a civic education assistant! I can't help with that, but I can definitely help you understand Indian elections, voter registration, or voting steps. What would you like to know?",
        "student": "I'm mainly here to teach election topics. I can help you learn about voting, EVMs, NOTA, or how elections work. What topic do you want to learn?",
        "elderly": "I can help with election questions. Please ask about voter registration, polling day, voter list, or EVM."
    }
}

def apply_tone_to_template(template_name: str, persona: str) -> str:
    """Returns the pre-written template text for the given persona."""
    norm_persona = normalize_persona(persona)
    templates = _TEMPLATES.get(template_name)
    if not templates:
        return ""
    return templates.get(norm_persona, templates.get("general", ""))


# ---------------------------------------------------------------------------
# Suggested Replies by Persona
# ---------------------------------------------------------------------------
_SUGGESTED_REPLIES = {
    # Default chips when no specific state active (e.g. out of scope)
    "default": {
        "general": ["Explain Step 1", "Check my name", "Find polling booth", "What ID do I carry?"],
        "first-time-voter": ["Explain the first step", "What is Form 6?", "I don't have Voter ID", "What should I do next?"],
        "student": ["Explain simply", "Give an example", "Why does this matter?", "Next step"],
        "elderly": ["Explain slowly", "Tell me next step", "What should I carry?", "Help me check my name"]
    },
    
    # For no_epic path follow-ups
    "no_epic_followups": {
        "general": ["Explain Step 1", "Explain Form 6", "Explain Step 3", "What ID do I carry?"],
        "first-time-voter": ["Explain the first step", "What is Form 6?", "What documents do I need?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "What is Form 6?", "Give an example"],
        "elderly": ["Explain slowly", "Tell me next step", "What is Form 6?", "What should I carry?"]
    },
    
    # For has_epic path follow-ups
    "has_epic_followups": {
        "general": ["How to check my name", "How to find my booth", "What ID do I carry", "Explain polling day"],
        "first-time-voter": ["How to check my name", "What should I do next?", "What ID do I carry", "Explain polling day"],
        "student": ["Explain simply", "Why does this matter?", "How to check my name", "Next step"],
        "elderly": ["Help me check my name", "Explain slowly", "What should I carry?", "Tell me next step"]
    },
    
    # For turning_18 path follow-ups
    "turning_18_followups": {
        "general": ["What documents do I need", "How do I fill Form 6", "What is the qualifying date"],
        "first-time-voter": ["What documents do I need", "What is Form 6?", "What is the qualifying date", "What should I do next?"],
        "student": ["Explain simply", "What is the qualifying date", "Why does this matter?", "Next step"],
        "elderly": ["Explain slowly", "What documents do I need", "Tell me next step"]
    },
    
    # For under_18 path follow-ups
    "under_18_followups": {
        "general": ["How do elections work", "What is EVM", "What is NOTA", "Election timeline"],
        "first-time-voter": ["How do elections work", "What is EVM", "What is NOTA", "Election timeline"],
        "student": ["Explain simply", "Give an example", "What is EVM", "Why does this matter?"],
        "elderly": ["Explain slowly", "What is EVM", "How do elections work"]
    },
    
    # For returning_voter follow-ups
    "returning_voter_followups": {
        "general": ["Check my name in voter list", "Find my polling booth", "What ID can I carry"],
        "first-time-voter": ["Check my name", "What should I do next?", "What ID can I carry"],
        "student": ["Explain simply", "Why does this matter?", "Check my name", "Next step"],
        "elderly": ["Help me check my name", "Explain slowly", "What should I carry?"]
    },

    "accepted_id_followups": {
        "general": ["How do I check my name?", "Find polling booth"],
        "first-time-voter": ["How do I check my name?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["Help me check my name", "Explain slowly"]
    },
    "voter_list_followups": {
        "general": ["What ID do I carry?", "Find polling booth"],
        "first-time-voter": ["What ID do I carry?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["What should I carry?", "Explain slowly"]
    },
    "form6_followups": {
        "general": ["How do I check my name?", "What ID do I carry?"],
        "first-time-voter": ["How do I check my name?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["Help me check my name", "Explain slowly"]
    },
    "epic_followups": {
        "general": ["How do I check my name?", "What ID do I carry?"],
        "first-time-voter": ["How do I check my name?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["Help me check my name", "Explain slowly"]
    },
    "booth_followups": {
        "general": ["What ID do I carry?", "Explain polling day"],
        "first-time-voter": ["What ID do I carry?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["What should I carry?", "Explain slowly"]
    },
    "polling_day_followups": {
        "general": ["What ID do I carry?", "What is EVM?"],
        "first-time-voter": ["What ID do I carry?", "What is EVM?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["What should I carry?", "Explain slowly"]
    },
    "evm_followups": {
        "general": ["Explain polling day", "What ID do I carry?"],
        "first-time-voter": ["Explain polling day", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["Explain slowly", "What should I carry?"]
    },
    "eligibility_followups": {
        "general": ["Explain Form 6", "What documents do I need?"],
        "first-time-voter": ["What is Form 6?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["Explain slowly", "Tell me next step"]
    },
    "docs_followups": {
        "general": ["Explain Form 6", "How do I track application?"],
        "first-time-voter": ["What is Form 6?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["Explain slowly", "Tell me next step"]
    },
    "tracking_followups": {
        "general": ["How do I check my name?", "What ID do I carry?"],
        "first-time-voter": ["How do I check my name?", "What should I do next?"],
        "student": ["Explain simply", "Why does this matter?", "Next step"],
        "elderly": ["Help me check my name", "Explain slowly"]
    }
}

def get_persona_suggested_replies(persona: str, default_key: str = "default") -> list[str]:
    """Returns the suggested replies for a given persona and flow state key."""
    norm_persona = normalize_persona(persona)
    reply_set = _SUGGESTED_REPLIES.get(default_key, _SUGGESTED_REPLIES["default"])
    return reply_set.get(norm_persona, reply_set.get("general", []))
