import asyncio
from app.services.source_router import classify_intent
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

queries = [
    'Who is current PM?',
    'Who is the current Prime Minister of India?',
    'Who is current President of India?',
    'Who is current Chief Minister of Goa?',
    'When is the next election?',
    'What is the latest ECI notification?',
    'Who is the current president of BJP?',
    'Who is the current head of Congress?',
    'Am I registered to vote?',
    'What is NOTA?'
]

for q in queries:
    res = classify_intent(q)
    intent = res.get('intent')
    msg = res.get('direct_response', '')
    if msg:
        msg = msg[:60].replace('\n', ' ')
    else:
        msg = "-> Passes to Gemini API"
    print(f"Q: {q}\nIntent: {intent}\nOutput: {msg}\n{'-'*60}")
