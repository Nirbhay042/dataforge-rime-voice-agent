# DataForge 2026 — PS2 Rime Project State

## Project
- Hackathon: DataForge 2026 — Rime Hackathon Challenge (PS2)
- Project: Voice Agent with Interruption & Recovery
- Status: Chat 1 — Planning complete
- Current phase: Planning / Setup

## Core Problem
Build a voice-native product where Rime-generated speech is essential, focused on the hard voice-engineering problem of interruption and recovery.

## Central Technical Claim
A voice agent can recover from mid-conversation interruptions without speaking stale information from the previous request.

## Acceptance Test
1. User gives a task that takes enough time for interruption.
2. Agent starts processing and/or speaking the response.
3. User interrupts and changes an important part of the request.
4. Current/stale Rime audio stops promptly.
5. The previous task/result is cancelled, invalidated, or reconciled so stale information is not spoken.
6. The updated instruction is processed.
7. The final spoken response reflects the user's latest request.

## Proposed Architecture
User
→ Voice Frontend
→ Speech Recognition
→ Agent/Orchestrator
→ Interruption Manager
   → cancel/invalidate old task
   → stop old audio
   → apply new instruction
→ Tools / Task execution
→ Rime TTS
→ Streaming Audio
→ User

## Initial Technology Stack
- Python
- FastAPI
- Rime TTS
- LiveKit Agents where appropriate for realtime transport/turn handling
- Web frontend
- Git/GitHub
- Automated acceptance tests

## Planned Repository Structure
dataforge-ps2-rime/
├── PROJECT_STATE.md
├── README.md
├── RIME_EVIDENCE.md
├── .env.example
├── .gitignore
├── backend/
│   ├── main.py
│   ├── agent/
│   ├── tools/
│   ├── voice/
│   └── state/
├── frontend/
├── tests/
│   ├── interruption_test.py
│   └── fixtures/
├── docs/
└── demo/

## Milestones
### Chat 1 — Planning & Setup
- [x] Select PS2
- [x] Define product direction
- [x] Define central claim
- [x] Define acceptance test
- [x] Draft architecture
- [x] Draft technology stack
- [x] Define project structure
- [x] Create PROJECT_STATE.md

### Chat 2 — Backend
- [x] Create backend project
- [x] Configure environment
- [x] Implement agent/orchestrator
- [x] Implement conversation state
- [x] Implement task IDs / cancellation or stale-result protection
- [x] Add initial tests

### Chat 3 — Voice
- [x] Verify current Rime API/integration documentation
- [x] Configure exact Rime model/voice/language
- [x] Implement Rime TTS
- [x] Implement streaming audio
- [x] Implement interruption handling
- [x] Verify old audio stops and new response takes priority

### Chat 4 — Frontend
- [x] Build voice UI
- [x] Add microphone input
- [x] Add live speech/output state
- [x] Add interruption controls/visual feedback
- [x] Connect frontend to backend

### Chat 5 — Testing & Evidence
- [x] Normal end-to-end test
- [x] Interruption test
- [x] Delayed-tool stress test
- [x] Multiple interruption test
- [x] Measure relevant performance/behavior
- [x] Record repeatable test procedure
- [x] Document limitations and failure cases
### Chat 6 — Submission
- [ ] README
- [ ] RIME_EVIDENCE.md
- [ ] Demo flow <= 4–5 minutes
- [ ] Architecture documentation
- [ ] Reproduction instructions
- [ ] Third-party services and licenses
- [ ] AI/code/data/asset disclosure
- [ ] Final pre-submission checklist

## Important Constraints
- Rime must be the primary spoken output in the judged flow.
- Voice must be essential to the product, not just a play button over a normal chatbot.
- The hard voice problem must be demonstrated, not merely described.
- Measurements must be honest and reproducible.
- Exact Rime model ID, speaker, language, endpoint, audio format, and transport will be documented once finalized.
- Secrets must never be committed to the repository.
- Cached vs uncached results must be distinguished where relevant.
- Any synthetic, precomputed, mocked, or reused component must be clearly disclosed.
- We must be able to explain and defend every major component.

## Current Decision
PS2 is the selected problem statement. The initial focus is interruption & recovery because it maps directly to the challenge's full-duplex/interruption acceptance test.

## Next Task
Start Chat 2 with backend setup and implementation.

## How to Continue in a New Chat
Upload the latest PROJECT_STATE.md and say:
"Continue my DataForge PS2 Rime project. Read PROJECT_STATE.md and continue from where we stopped."