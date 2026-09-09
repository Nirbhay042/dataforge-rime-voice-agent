# Rime Evidence — DataForge Voice Agent

## Project

**Project Name:** DataForge  
**Hackathon:** Rime Hackathon 2026  
**Problem Statement:** PS2 — Voice Agent with Interruption & Recovery

---

## 1. Purpose

This document provides evidence of the integration and use of **Rime TTS** in the DataForge voice agent.

DataForge uses Rime as its text-to-speech engine to convert AI-generated text into spoken audio and stream/play the resulting voice response.

---

## 2. Rime Integration

The project contains a dedicated Rime module:

```text
backend/
└── voice/
    └── rime_tts.py
```

The `RimeTTS` class communicates with the Rime TTS API.

The Rime API key is loaded through an environment variable:

```env
RIME_API_KEY=your_rime_api_key
```

The API key is not hard-coded into the frontend or source code.

---

## 3. Rime API Configuration

The Rime TTS integration uses:

```text
https://users.rime.ai/v1/rime-tts
```

Request headers include:

```text
Authorization: Bearer <RIME_API_KEY>
Content-Type: application/json
Accept: audio/webm;codecs=opus
```

Example TTS configuration:

```python
{
    "text": text,
    "modelId": "mistv3",
    "speaker": "cove",
    "lang": "eng",
    "samplingRate": 24000
}
```

---

## 4. Rime TTS Implementation

DataForge provides two Rime operations.

### Normal Synthesis

The `synthesize()` method sends text to Rime and returns generated audio bytes.

```text
Gemini Response
      ↓
Text
      ↓
Rime TTS
      ↓
Audio Bytes
      ↓
Frontend
```

### Streaming Synthesis

The `stream()` method uses asynchronous HTTP streaming.

```text
Gemini Text
     ↓
Sentence
     ↓
Rime Streaming TTS
     ↓
Audio Chunks
     ↓
Frontend Audio Playback
```

This allows audio data to be received as a stream.

---

## 5. FastAPI Rime Endpoints

### Streaming Endpoint

```http
GET /audio/stream?text=Hello
```

Flow:

```text
Frontend
   ↓
/audio/stream
   ↓
RimeTTS.stream()
   ↓
Rime API
   ↓
Audio chunks
   ↓
Frontend
```

### Audio Chunk Endpoint

```http
GET /audio/chunk?text=Hello
```

Flow:

```text
Frontend
   ↓
/audio/chunk
   ↓
RimeTTS.synthesize()
   ↓
Rime API
   ↓
Audio
   ↓
Frontend
```

---

## 6. Sentence-by-Sentence Voice Pipeline

Gemini responses are streamed as text.

The frontend identifies completed sentences and sends them to Rime TTS.

```text
Gemini text stream
       ↓
Sentence detection
       ↓
Rime TTS
       ↓
Audio queue
       ↓
Playback
```

This allows DataForge to begin speaking before the complete AI response has been generated.

---

## 7. Interruption and Rime Audio Cancellation

Rime is directly involved in the interruption/recovery flow.

When DataForge is speaking and the user interrupts:

```text
User speaks
    ↓
Interruption detected
    ↓
Stop current Rime audio
    ↓
Clear audio queue
    ↓
Cancel old Gemini task
    ↓
Invalidate old response
    ↓
Process latest instruction
    ↓
Generate new response
    ↓
Rime TTS
    ↓
Play new response
```

This prevents old audio from continuing after the user changes the request.

---

## 8. Example Interruption Test

### Initial Request

```text
Explain artificial intelligence.
```

DataForge starts generating and speaking the response using Gemini + Rime.

### User Interruption

While DataForge is speaking:

```text
Stop. Explain robotics instead.
```

Expected behavior:

```text
Old Rime audio
      ↓
STOPPED

Old audio queue
      ↓
CLEARED

Old Gemini task
      ↓
CANCELLED

Old response
      ↓
INVALIDATED

New request
      ↓
PROCESSED

New Gemini response
      ↓
Rime TTS

New audio
      ↓
PLAYED
```

The final spoken response should be about robotics.

---

## 9. Evidence Checklist

### Source Code Evidence

- [x] `backend/voice/rime_tts.py`
- [x] Rime API integration
- [x] Rime API key loaded through environment variable
- [x] Rime streaming method
- [x] Rime synthesis method
- [x] FastAPI Rime streaming endpoint
- [x] FastAPI Rime audio endpoint

### Runtime Evidence

- [ ] Rime TTS successfully generates audio
- [ ] Audio is received by the frontend
- [ ] DataForge speaks the generated response
- [ ] Audio queue plays responses sequentially
- [ ] Current audio stops during interruption
- [ ] Old queued audio is cleared
- [ ] New response is generated and spoken

---

## 10. Recommended Screenshot Evidence

For the final submission, add screenshots showing:

1. DataForge frontend while the agent is speaking.
2. Rime-related backend terminal logs.
3. `backend/voice/rime_tts.py`.
4. An interruption during playback.
5. The new response after interruption.
6. Project structure showing `backend/voice/rime_tts.py`.

Suggested repository structure:

```text
docs/
└── screenshots/
    ├── rime-speaking.png
    ├── interruption.png
    └── recovered-response.png
```

---

## 11. Recommended Demo Evidence

Record the following sequence for the hackathon demo:

```text
STEP 1
User:
"Explain artificial intelligence."

STEP 2
DataForge starts speaking.

STEP 3
User interrupts:
"Stop. Explain robotics instead."

STEP 4
Current Rime audio stops.

STEP 5
Old Gemini task is cancelled.

STEP 6
New robotics request is processed.

STEP 7
Rime generates speech for the new response.

STEP 8
DataForge speaks the new response.
```

This demonstrates that Rime is part of the active voice pipeline and that the application can stop and recover from an interrupted response.

---

## 12. Security Evidence

The Rime API key is loaded from:

```env
RIME_API_KEY=your_rime_api_key
```

The `.env` file should be excluded from Git:

```gitignore
.env
```

Never publish the actual API key in:

- GitHub
- README files
- Screenshots
- Demo videos
- Public presentations

---

## 13. Rime's Role in the Architecture

Rime is responsible for the **Text-to-Speech layer**.

Complete voice pipeline:

```text
                    USER
                      │
                      ▼
              Speech Recognition
                      │
                      ▼
                  FastAPI
                      │
                      ▼
              Agent Orchestrator
                      │
                      ▼
               Gemini Streaming
                      │
                      ▼
                Text Chunks
                      │
                      ▼
              Sentence Detection
                      │
                      ▼
                  RIME TTS
                      │
                      ▼
                Audio Chunks
                      │
                      ▼
                Audio Queue
                      │
                      ▼
                User Hears
```

---

## 14. Why Rime Is Important

Rime provides the speech-generation component that turns DataForge from a text chatbot into a voice agent.

The project combines:

```text
Speech Recognition
        +
Gemini AI
        +
Rime TTS
        +
Audio Streaming
        +
Interruption Management
```

Together, these components enable a voice-first conversational experience.

---

## 15. Evidence Summary

DataForge integrates Rime TTS as a core component of its voice response pipeline.

The integration supports:

- Text-to-speech generation
- Streaming audio
- Audio playback
- Sentence-based speech generation
- Audio queue management
- Interruption handling
- Stopping stale audio
- Recovery with the latest user instruction

The Rime integration is directly connected to the project's primary PS2 capability:

> **Voice Agent with Interruption & Recovery**

---

## 16. Final Demonstration Statement

**DataForge uses Rime TTS to provide real-time spoken responses and integrates Rime audio playback with its interruption-aware orchestration system. When a user interrupts the agent, the current audio is stopped, stale queued audio is cleared, the previous AI task is cancelled, and the latest instruction is processed before generating a new Rime-powered response.**

---

## Project Repository

Add the final repository URL here:

```text
YOUR_GITHUB_REPOSITORY_URL
```

## Demo Video

Add the final demo video URL here:

```text
YOUR_DEMO_VIDEO_URL
```

---

**DataForge — Voice intelligence that listens, speaks, and knows when to stop.**
