import asyncio
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, Response
from pydantic import BaseModel

from backend.agent.orchestrator import AgentOrchestrator


# ===============================
# FASTAPI APP
# ===============================

app = FastAPI(
    title="DataForge PS2 Rime Voice Agent",
    version="0.1.0"
)


# ===============================
# CORS
# ===============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===============================
# ORCHESTRATOR
# ===============================

orchestrator = AgentOrchestrator()


# ===============================
# REQUEST MODEL
# ===============================

class UserInstruction(BaseModel):
    conversation_id: str
    instruction: str


# ===============================
# ROOT
# ===============================

@app.get("/")
async def root():
    return {
        "project": "DataForge 2026 PS2",
        "status": "backend running"
    }


# ===============================
# INSTRUCTION STREAM
# ===============================

@app.post("/instruction")
async def instruction(request: UserInstruction):

    async def response_generator():
        try:
            async for chunk in orchestrator.stream_instruction(
                request.conversation_id,
                request.instruction
            ):
                # Convert Python dictionary
                # into NDJSON line
                yield json.dumps(chunk) + "\n"

        except asyncio.CancelledError:
            print("🛑 Instruction HTTP stream cancelled")
            return

    return StreamingResponse(
        response_generator(),
        media_type="application/x-ndjson"
    )


# ===============================
# RIME AUDIO STREAM
# ===============================

@app.get("/audio/stream")
async def stream_audio(text: str):

    async def audio_generator():
        async for chunk in orchestrator.rime_tts.stream(text):
            yield chunk

    return StreamingResponse(
        audio_generator(),
        media_type="audio/webm"
    )


# ===============================
# RIME AUDIO CHUNK
# ===============================

@app.get("/audio/chunk")
async def audio_chunk(text: str):

    audio = await orchestrator.rime_tts.synthesize(text)

    return Response(
        content=audio,
        media_type="audio/webm"
    )


# ===============================
# AUDIO FILE
# ===============================

@app.get("/audio/{filename}")
async def get_audio(filename: str):

    audio_path = Path(filename)

    if not audio_path.exists():
        return {
            "status": "error",
            "message": "Audio file not found"
        }

    return FileResponse(
        path=audio_path,
        media_type="audio/webm"
    )