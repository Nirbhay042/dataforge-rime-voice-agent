# DataForge — Voice Intelligence Agent

> **Rime Hackathon 2026 — PS2: Voice Agent with Interruption & Recovery**

DataForge is a real-time, voice-native AI assistant designed to handle **mid-conversation interruptions and changing user instructions** without continuing to speak stale information.

The core idea is simple:

**Listen → Understand → Respond → Detect Interruption → Stop Old Response → Process Latest Instruction → Respond Again**

---

## 🎯 Problem Statement

Traditional voice assistants can continue processing or speaking an outdated response even after the user interrupts or changes their request.

For example:

1. User: **"Explain artificial intelligence."**
2. DataForge starts generating and speaking the answer.
3. User interrupts: **"Stop. Explain robotics instead."**
4. DataForge immediately stops the old audio and invalidates the old request.
5. The new robotics request becomes the active instruction.
6. DataForge responds only to the latest request.

This prevents **stale audio, stale AI responses, and conflicting tasks**.

---

## 💡 Solution

DataForge uses an interruption-aware orchestration system.

When a new instruction is detected:

- The currently playing Rime audio is stopped.
- The frontend clears queued audio.
- The previous Gemini task is cancelled.
- A new request version is created.
- Older/stale Gemini responses are ignored.
- The latest instruction is processed.
- The new response is streamed to the frontend.
- Rime converts the response into speech.
- Audio is played sentence-by-sentence.

The result is a more natural full-duplex voice interaction.

---

## ✨ Key Features

### 🎙️ Voice Interaction

- Browser-based microphone input
- Continuous speech recognition
- Voice-first interface
- Real-time conversation experience

### ⚡ Streaming AI Response

- Gemini streaming responses
- Text chunks are forwarded as they arrive
- First-token latency monitoring
- Minimal thinking configuration for latency-sensitive interaction

### 🛑 Interruption & Recovery

- Detects user speech while the agent is speaking
- Stops current audio immediately
- Cancels the active Gemini task
- Invalidates stale responses
- Processes the newest instruction
- Supports repeated interruptions

### 🔊 Rime TTS

- Rime TTS integration
- Streaming audio endpoint
- Audio chunk endpoint
- Sentence-by-sentence speech playback
- Queued audio playback

### 🧠 Conversation Context

- Maintains conversation history
- Keeps recent conversation messages
- Supports contextual follow-up questions
- Uses request versioning to protect against stale responses

### 🛡️ Fast Failure Handling

- Primary Gemini model:
  `gemini-2.5-flash-lite`
- Configurable fallback model
- 3-second first-token timeout
- 503 / overload detection
- Avoids long retry loops
- User-friendly error responses

### 🖥️ Voice UI

- DataForge voice interface
- Central voice orb
- Microphone control
- Stop button
- Live session interface
- Conversation cards
- Voice waveform visuals
- Rime engine status
- Responsive frontend layout

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │        USER          │
                    │   Voice Instruction  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   VOICE FRONTEND     │
                    │ HTML + CSS + JS      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ SPEECH RECOGNITION   │
                    │ Browser Web Speech   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    FASTAPI SERVER    │
                    │    /instruction      │
                    └──────────┬───────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │       AGENT ORCHESTRATOR        │
              │                                 │
              │  • Conversation State           │
              │  • Task Cancellation             │
              │  • Request Versioning            │
              │  • Stale Response Protection     │
              │  • Gemini Streaming              │
              └───────────────┬─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
          ┌─────────────────┐   ┌─────────────────┐
          │  Gemini 3.6     │   │ Fallback Model  │
          │  Flash          │   │ Configurable    │
          └────────┬────────┘   └────────┬────────┘
                   │                     │
                   └──────────┬──────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │      RIME TTS        │
                    │   Text → Speech      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   AUDIO PLAYBACK     │
                    │ Sentence Queue       │
                    └──────────┬───────────┘
                               │
                               ▼
                         USER HEARS
```

---

## 🔄 Interruption Flow

```text
User asks question
       │
       ▼
Gemini starts processing
       │
       ▼
Response starts streaming
       │
       ▼
Rime starts speaking
       │
       ▼
User interrupts
       │
       ├──► Stop current audio
       │
       ├──► Clear audio queue
       │
       ├──► Cancel old Gemini task
       │
       ├──► Increment request version
       │
       └──► Ignore stale response
                    │
                    ▼
            Process latest request
                    │
                    ▼
              Gemini response
                    │
                    ▼
                 Rime TTS
                    │
                    ▼
              New audio plays
```

---

## 📁 Project Structure

```text
DATAFORGE/
│
├── backend/
│   │
│   ├── agent/
│   │   └── orchestrator.py
│   │
│   ├── voice/
│   │   └── rime_tts.py
│   │
│   └── main.py
│
├── frontend/
│   │
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── .env
├── .gitignore
└── README.md
```

### Backend

#### `backend/main.py`

FastAPI application containing:

- Root health endpoint
- Instruction streaming endpoint
- Rime audio streaming endpoint
- Rime audio chunk endpoint
- Audio file endpoint
- CORS configuration

#### `backend/agent/orchestrator.py`

The main intelligence/orchestration layer.

Responsible for:

- Gemini communication
- Streaming responses
- Conversation state
- Task cancellation
- Request versioning
- Stale response protection
- Fallback model handling
- First-token timeout
- Error handling

#### `backend/voice/rime_tts.py`

Handles Rime text-to-speech operations:

- TTS synthesis
- Streaming TTS
- Rime API communication

### Frontend

#### `frontend/index.html`

Contains the DataForge voice interface.

#### `frontend/style.css`

Controls the visual design and animations.

#### `frontend/app.js`

Handles:

- Microphone interaction
- Speech recognition
- Backend communication
- Streaming response parsing
- Sentence extraction
- Rime audio playback
- Audio queue
- Interruption detection
- Audio cancellation
- UI state updates

---

## 🧰 Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python |
| API Framework | FastAPI |
| AI Model | Gemini 3.6 Flash |
| Fallback | Configurable Gemini model |
| Text-to-Speech | Rime TTS |
| Speech Recognition | Browser Web Speech API |
| Streaming | NDJSON + HTTP Streaming |
| Async Processing | Python asyncio |
| Environment | python-dotenv |
| HTTP Client | httpx |

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
RIME_API_KEY=your_rime_api_key
```

Do **not** commit real API keys to GitHub.

Add `.env` to `.gitignore`:

```gitignore
.env
__pycache__/
*.pyc
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd DATAFORGE
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn google-genai python-dotenv httpx
```

### 4. Configure environment variables

Create `.env`:

```env
GEMINI_API_KEY=your_key_here
RIME_API_KEY=your_key_here
```

---

## ▶️ Running the Backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

The backend will run at:

```text
http://127.0.0.1:8000
```

Health check:

```text
GET /
```

Expected response:

```json
{
  "project": "DataForge 2026 PS2",
  "status": "backend running"
}
```

---

## 🌐 Running the Frontend

Serve the `frontend` directory using a local HTTP server.

For example:

```bash
cd frontend
python -3.13 -m http.server 5500
```

Then open:

```text
http://127.0.0.1:5500
```

Using a local server is recommended instead of opening the HTML file directly because browser microphone and API behavior can depend on the page origin.

---

## ⚙️ Model Configuration

The primary model is configured in:

```text
backend/agent/orchestrator.py
```

Primary model:

```python
GEMINI_MODEL = "gemini-3.5-flash-lite"
```

Fallback model:

```python
FALLBACK_MODEL = "gemini-2.5-flash-lite"
```

To change the fallback, change only the fallback line.

Example:

```python
FALLBACK_MODEL = "YOUR_FALLBACK_MODEL"
```

---

## ⏱️ First-Token Protection

DataForge uses a first-token timeout:

```python
FIRST_TOKEN_TIMEOUT = 3.0
```

If the primary model does not provide the first response chunk within the configured timeout, DataForge switches to the fallback model.

This prevents the voice agent from waiting indefinitely before starting its response.

---

## 🛑 Stale Response Protection

Each request receives a version number:

```text
Request 1 → version 1
Request 2 → version 2
Request 3 → version 3
```

If version 1 is still producing data after version 2 becomes active, version 1 is treated as stale.

Only the current version is allowed to update the conversation.

This is one of the core mechanisms behind interruption recovery.

---

## 🔊 Audio Queue

Gemini responses are streamed as text.

The frontend collects complete sentences and sends them to Rime TTS.

Conceptually:

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

This allows the agent to start speaking before the complete response has been generated.

---

## 🎙️ Example Demo

### Initial request

**User:**

> Explain artificial intelligence.

DataForge starts speaking.

### Interruption

**User:**

> Stop! Explain robotics instead.

DataForge:

- stops the old audio
- clears queued audio
- cancels the old Gemini task
- invalidates the old response
- processes the new request

### Second interruption

**User:**

> No, tell me about humanoid robots.

The latest instruction becomes the active task.

The final response should correspond to:

> Humanoid robots

and not the earlier requests.

---

## 🧪 Acceptance Test

### Test 1 — Normal Request

**Input:**

> What is artificial intelligence?

**Expected:**

- Gemini generates response
- Rime speaks response
- No interruption occurs

---

### Test 2 — Interrupt During AI Processing

**Input:**

> Explain machine learning in detail.

Interrupt quickly:

> Stop. Explain robotics.

**Expected:**

- Old request is cancelled
- New request is processed
- Final answer is about robotics

---

### Test 3 — Interrupt During Audio Playback

Allow DataForge to start speaking.

Then say:

> Stop. Tell me about quantum computing.

**Expected:**

- Current Rime audio stops promptly
- Queued old audio is cleared
- New request is processed
- New response is spoken

---

### Test 4 — Multiple Interruptions

Example:

```text
Explain AI.
       ↓
Stop, explain robotics.
       ↓
No, explain humanoid robots.
```

**Expected:**

Only the latest instruction should determine the final response.

---

### Test 5 — Stale Response

An old Gemini response must not overwrite a newer request.

**Expected:**

```text
Old version → ignored
Current version → accepted
```

---

### Test 6 — Gemini Overload

If the primary Gemini request receives a temporary 503/overload-type error:

**Expected:**

```text
Primary Gemini
      ↓
503 / overload
      ↓
Fallback model
      ↓
Response
```

No long retry loop should occur.

---

## 🛡️ Security

Never expose API keys in:

- `index.html`
- `app.js`
- GitHub
- screenshots
- public documentation

Use environment variables:

```env
GEMINI_API_KEY=
RIME_API_KEY=
```

Make sure `.env` is included in `.gitignore`.

If an API key is accidentally pushed to a public repository, revoke/rotate it immediately.

---

## 📊 Why DataForge Is Different

The important feature is not simply generating an AI response.

The system is designed around **interruptibility**.

Traditional flow:

```text
User
 ↓
AI processing
 ↓
AI response
 ↓
Audio
```

DataForge flow:

```text
User
 ↓
AI processing
 ↓
Streaming response
 ↓
Audio
 ↓
User interruption
 ↓
Cancel
 ↓
Invalidate
 ↓
Recover
 ↓
Latest request
 ↓
New response
```

This makes the interaction closer to a natural human conversation.

---

## 🔮 Future Improvements

Potential future extensions include:

- Lower-latency speech recognition
- Native real-time audio model integration
- More advanced interruption detection
- Voice activity detection
- Better echo cancellation
- Persistent conversation storage
- Authentication
- Multi-user sessions
- Tool calling
- External data retrieval
- Analytics dashboard
- Automated end-to-end acceptance tests
- Production deployment
- Mobile application
- Advanced conversation summarization

---

## ⚠️ Current Limitations

- Browser speech recognition availability varies by browser.
- Local development currently uses HTTP.
- API availability and model capacity can affect response latency.
- Voice interruption detection depends partly on microphone/audio conditions.
- Rime TTS requires a valid Rime API key.
- Gemini requires a valid API key and available model access.
- The current conversation state is held in application memory.

---

## 🏆 Hackathon Value

DataForge demonstrates several important real-time AI engineering concepts:

- Voice-first interaction
- Streaming AI
- Streaming TTS
- Asynchronous task management
- Cancellation
- Request versioning
- Stale-response prevention
- Interruption recovery
- Graceful fallback
- Full-duplex interaction design

The key innovation is the **interruption-aware orchestration layer**, which coordinates the AI task, response stream, and audio playback so that the system can recover when the user changes their mind mid-response.

---

## 📜 License

Add your preferred license here before publishing the project.

Example:

```text
MIT License
```

---

## 👥 Project

**Project:** DataForge  
**Track:** Rime Hackathon 2026  
**Problem Statement:** PS2 — Voice Agent with Interruption & Recovery

Built with:

- Python
- FastAPI
- Gemini
- Rime TTS
- HTML
- CSS
- JavaScript

---

## ⭐ Final Demo Goal

The ideal demonstration should show:

```text
LISTEN
  ↓
UNDERSTAND
  ↓
RESPOND
  ↓
SPEAK
  ↓
INTERRUPT
  ↓
STOP OLD RESPONSE
  ↓
CANCEL OLD TASK
  ↓
PROCESS NEW REQUEST
  ↓
RESPOND TO LATEST REQUEST
```

**DataForge — Voice intelligence that listens, speaks, and knows when to stop.**
