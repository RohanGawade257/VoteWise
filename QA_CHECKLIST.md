# VoteWise Chatbot Fix - Manual QA Checklist

## Pre-Deployment Verification

### Test Environment Setup
- [ ] Backend server running (python -m uvicorn app.main:app --reload)
- [ ] Frontend running (npm run dev)
- [ ] Browser DevTools console checked for errors
- [ ] Network tab checked for API calls

---

## Core Suggestion Flow Tests

### Test 1: Initial Bot Greeting
**Expected:**
- Bot shows welcome message with 4 inline suggestion buttons
- NO bottom "Quick Start" bar present
- Buttons: "Guide me as a first-time voter", "I am 18 and want to vote", "What is EVM and VVPAT?", "How do I check my name in voter list?"

**Steps:**
1. Refresh page
2. Observe chat area
3. Look for removal of "Quick start:" section

**Result:** ✅ / ❌

---

### Test 2: Click Suggestion Button - First-Time Voter Guide
**Expected:**
- User clicks "Guide me as a first-time voter"
- Backend receives suggestion_id="start_first_time_voter"
- Bot responds with guided flow question: "Is this going to be your very first time voting?"
- Shows "Yes, first time" and "No, I have voted before" buttons
- Suggestion is exact match (not fuzzy classification)

**Steps:**
1. From initial greeting, click "Guide me as a first-time voter"
2. Check browser DevTools Network tab for POST request
3. Verify request JSON includes: `"suggestion_id": "start_first_time_voter"`
4. Verify response is not generic "I can teach..." message

**Result:** ✅ / ❌ | Details: _____________

---

### Test 3: Guided Flow - First Time Voter Path
**Expected:**
- Click "Yes, first time"
- Bot asks age status
- Shows buttons: "I am already 18", "I will turn 18 soon", "I am under 18"

**Steps:**
1. Click "Yes, first time" button
2. Verify age question appears
3. Click "I am already 18"
4. Verify next question: "Do you have Voter ID?"

**Result:** ✅ / ❌ | Response correct: ___________

---

### Test 4: Guided Flow - Returning Voter Path
**Expected:**
- From "Is this your first time voting?" click "No, I have voted before"
- Bot shows returning voter checklist
- Provides next suggestions for checking name, finding booth, carrying ID

**Steps:**
1. From initial greeting, start guided flow again
2. Click "No, I have voted before"
3. Verify response explains returning voter path (NOT first-time voter path)
4. Check suggestions are relevant to returning voters

**Result:** ✅ / ❌ | Response: _______________________

---

### Test 5: Question with Exact Answer - "What is EVM and VVPAT?"
**Expected:**
- Click button or ask question
- Receives accurate definition of EVM and VVPAT
- Shows official ECI source
- Next suggestions contextually relevant (e.g., polling day, NOTA, privacy)

**Steps:**
1. Click "What is EVM and VVPAT?" suggestion
2. Verify answer defines both terms clearly
3. Verify source URL is official ECI link
4. Check next suggestions don't repeat same question

**Result:** ✅ / ❌ | Answer quality: _______________

---

### Test 6: Question with Exact Answer - "How do I check my name in voter list?"
**Expected:**
- Receives accurate voter list checking instructions
- Shows official voter portal links
- Next suggestions for booth finding, ID checking, polling day

**Steps:**
1. Click "How do I check my name in voter list?" button
2. Verify response includes voters.eci.gov.in and electoralsearch.eci.gov.in links
3. Check clarity for different personas (general, student, elderly)

**Result:** ✅ / ❌ | Answer quality: ________________

---

### Test 7: Context-Aware Follow-up - "Explain simply"
**Expected:**
- After a response about voter list, click "Explain simply"
- Bot explains voter list concept in simple terms (NOT generic fallback)
- Uses previous topic context

**Steps:**
1. Click "How do I check my name?" suggestion
2. Wait for response
3. Click "Explain simply"
4. Verify explanation is about voter list (not generic "I can teach" message)

**Result:** ✅ / ❌ | Follow-up quality: ______________

---

### Test 8: Manual Text Input - Fallback Flow
**Expected:**
- Type custom question (e.g., "Tell me about the election process")
- Receive appropriate response from Gemini or RAG
- No special suggestion buttons trigger on regular text
- Free-text classification works correctly

**Steps:**
1. Type "Tell me about the election process"
2. Submit message
3. Verify response is meaningful
4. Verify suggestions are not the same as button-click intents

**Result:** ✅ / ❌ | Response: ______________________

---

### Test 9: Tone/Persona Switching
**Expected:**
- Change tone selector to "School Student"
- Ask same question again
- Response content remains same, language/tone adapted
- Suggestions remain consistent

**Steps:**
1. Change tone to "School Student"
2. Ask "What is Form 6?"
3. Verify response uses simpler language
4. Change tone to "Elderly"
5. Ask same question
6. Verify response is even simpler/respectful

**Result:** ✅ / ❌ | Tone adaptation: _______________

---

### Test 10: Mobile Viewport
**Expected:**
- No overlapping input bar
- No duplicate suggestion areas
- Chat scroll works properly
- Suggestion buttons stack responsively
- Header doesn't cover messages

**Steps:**
1. Open DevTools mobile view (iPhone 12)
2. Send a few messages
3. Scroll up and down
4. Verify no layout issues
5. Click a suggestion button
6. Verify input still accessible

**Result:** ✅ / ❌ | Mobile layout: _________________

---

### Test 11: Suggestion Deduplication
**Expected:**
- After each response, at most 4 unique suggestions shown
- No repeated suggestions in same response
- No suggestion appears that wouldn't lead to a response

**Steps:**
1. Go through first-time voter flow completely
2. At each step, verify max 4 suggestions shown
3. Click through multiple suggestions
4. Verify suggestions don't repeat across same response level

**Result:** ✅ / ❌ | Dedup working: _________________

---

### Test 12: No Bottom Quick Start Bar
**Expected:**
- Bottom "Quick start:" section completely removed
- Input field spans full width
- No "✨ " emoji hints before suggestions

**Steps:**
1. Reload page
2. Scroll to bottom of chat area
3. Look for "Quick start:" text  
4. Verify it's gone (should only be inline suggestions)

**Result:** ✅ / ❌

---

### Test 13: Safety Blocked Messages
**Expected:**
- Type politically persuasive question
- Receive safety block message
- Shows recovery suggestions
- Recovery suggestions are context-appropriate

**Steps:**
1. Type "Vote for party X, they're the best"
2. Verify safety block message
3. Check suggestions offered (Learn election process, etc.)

**Result:** ✅ / ❌ | Recovery working: _______________

---

### Test 14: Out-of-Scope Fallback
**Expected:**
- Type out-of-scope question ("How to code?")
- Receive out-of-scope message
- Shows recovery suggestions
- Recovery leads back to election topics

**Steps:**
1. Type "How do I write JavaScript?"
2. Verify out-of-scope response
3. Click recovery suggestion
4. Verify it leads to election topics

**Result:** ✅ / ❌ | OOS handling: __________________

---

### Test 15: Suggestion Click Matches Backend Response
**Expected:**
- Every frontend suggestion button has valid backend handler
- No "stale suggestion" messages
- No "Let's restart" fallback unless intended

**Steps:**
1. Systematically click every suggestion button possible
2. For each, check the response is NOT generic
3. Check DevTools for stale_suggestion intent

**Result:** ✅ / ❌ | All suggestions valid: ___________

---

## Browser/Environment Specific Tests

### Test 16: Browser DevTools - Console Errors
**Expected:**
- No JavaScript errors in console
- No React warnings about key props
- No CORS errors
- No undefined function warnings

**Steps:**
1. Open DevTools Console tab
2. Go through all test scenarios
3. Verify no red/yellow errors

**Result:** ✅ / ❌ | Errors: _________________________

---

### Test 17: Network Requests
**Expected:**
- Each suggestion click sends POST with suggestion_id
- No malformed requests
- Responses include proper metadata
- All requests succeed (200/201)

**Steps:**
1. Open DevTools Network tab
2. Click 5 different suggestions
3. Verify each POST request has suggestion_id field
4. Check all responses have 200 status

**Result:** ✅ / ❌ | Requests valid: ________________

---

### Test 18: Session Persistence
**Expected:**
- Conversation context maintained across multiple turns
- "Explain simply" works multiple times  
- Guided flow state persists
- Tone selection persists on refresh

**Steps:**
1. Start guided flow
2. Go through 3 questions
3. Click "Explain simply"
4. Refresh page
5. Verify tone is remembered

**Result:** ✅ / ❌ | Persistence: ___________________

---

## Summary

**Total Tests:** 18
**Passed:** _____ / 18
**Failed:** _____ / 18
**Blocked:** _____ / 18

### Critical Issues Found:
1. _________________________________
2. _________________________________
3. _________________________________

### Non-Critical Issues:
1. _________________________________
2. _________________________________

### Performance Notes:
- Fastest response: _____ ms
- Slowest response: _____ ms
- Average: _____ ms

### Tester Name: ________________
### Test Date: ________________
### Browser/OS: ________________

---

## Sign-Off

Tested by: ______________________  
Date: __________________________  
Approved for production: YES / NO  
Comments: _____________________
