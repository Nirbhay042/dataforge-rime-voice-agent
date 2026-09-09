import asyncio
import uuid
import os
import time
from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

from backend.voice.rime_tts import RimeTTS


load_dotenv()


# ======================================================
# GEMINI CLIENT
# ======================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set.")


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ======================================================
# GEMINI MODEL
# ======================================================

# Current model
GEMINI_MODEL = "gemini-3.5-flash-lite"


# ======================================================
# THINKING CONFIG
# ======================================================
#
# Gemini 3.x:
#   minimal / low / medium / high
#
# We use MINIMAL because this is a
# latency-sensitive voice agent.
#
# Later, if you switch to Gemini 2.5 Flash-Lite,
# change only GEMINI_MODEL and this config
# will automatically use the correct setting.
#
# ======================================================

def get_gemini_config():

    # --------------------------------------------------
    # Gemini 3.x models
    # --------------------------------------------------

    if GEMINI_MODEL.startswith("gemini-3"):

        return types.GenerateContentConfig(

            thinking_config=types.ThinkingConfig(
                thinking_level="minimal"
            )

        )

    # --------------------------------------------------
    # Gemini 2.5 models
    # --------------------------------------------------

    elif GEMINI_MODEL.startswith("gemini-2.5"):

        return types.GenerateContentConfig(

            thinking_config=types.ThinkingConfig(
                thinking_budget=0
            )

        )

    # --------------------------------------------------
    # Fallback
    # --------------------------------------------------

    return types.GenerateContentConfig()


# ======================================================
# CONVERSATION STATE
# ======================================================

@dataclass
class ConversationState:

    conversation_id: str

    current_task_id: Optional[str] = None

    latest_user_instruction: Optional[str] = None

    task: Optional[asyncio.Task] = None

    response_version: int = 0

    conversation_history: list = None

    def __post_init__(self):

        if self.conversation_history is None:

            self.conversation_history = []

    def new_instruction(self, instruction: str):

        self.latest_user_instruction = instruction

        self.response_version += 1

    def is_current(self, version: int) -> bool:

        return version == self.response_version


# ======================================================
# AGENT ORCHESTRATOR
# ======================================================

class AgentOrchestrator:

    def __init__(self):

        self.rime_tts = RimeTTS()

        self.conversations = {}


    # ==================================================
    # GET CONVERSATION
    # ==================================================

    def get_conversation(
        self,
        conversation_id: str
    ):

        if conversation_id not in self.conversations:

            self.conversations[conversation_id] = (
                ConversationState(
                    conversation_id=conversation_id
                )
            )

        return self.conversations[conversation_id]


    # ==================================================
    # CANCEL CURRENT TASK
    # ==================================================

    async def _cancel_current_task(
        self,
        state: ConversationState
    ):

        old_task = state.task

        if old_task and not old_task.done():

            print(
                "🛑 Cancelling previous Gemini task..."
            )

            old_task.cancel()

            try:

                await old_task

            except asyncio.CancelledError:

                pass

            except Exception as error:

                print(
                    "⚠️ Previous task error:",
                    error
                )


    # ==================================================
    # STREAM INSTRUCTION
    # ==================================================

    async def stream_instruction(
        self,
        conversation_id: str,
        instruction: str
    ):

        state = self.get_conversation(
            conversation_id
        )

        # ----------------------------------------------
        # Cancel previous request
        # ----------------------------------------------

        await self._cancel_current_task(
            state
        )

        # ----------------------------------------------
        # Create new request version
        # ----------------------------------------------

        state.new_instruction(
            instruction
        )

        version = state.response_version

        task_id = str(
            uuid.uuid4()
        )

        state.current_task_id = task_id

        print()
        print("=" * 60)

        print(
            f"🧠 Processing instruction "
            f"version={version}"
        )

        print(
            f"🤖 Model: {GEMINI_MODEL}"
        )

        print(
            "⚡ Thinking: MINIMAL"
        )

        print("=" * 60)

        # ----------------------------------------------
        # Queue for streaming chunks
        # ----------------------------------------------

        queue = asyncio.Queue()

        # ----------------------------------------------
        # Start Gemini worker
        # ----------------------------------------------

        task = asyncio.create_task(

            self._gemini_stream_worker(

                state=state,

                instruction=instruction,

                version=version,

                task_id=task_id,

                queue=queue

            )

        )

        state.task = task

        try:

            while True:

                item = await queue.get()

                # --------------------------------------
                # End of stream
                # --------------------------------------

                if item is None:

                    break

                # --------------------------------------
                # Yield chunk to FastAPI
                # --------------------------------------

                yield item

        except asyncio.CancelledError:

            print(
                f"🛑 Frontend stream cancelled "
                f"version={version}"
            )

            if not task.done():

                task.cancel()

                try:

                    await task

                except asyncio.CancelledError:

                    pass

            raise

        finally:

            # ------------------------------------------
            # Cleanup only if this is still
            # the active task
            # ------------------------------------------

            if state.task is task:

                state.task = None


    # ==================================================
    # GEMINI STREAM WORKER
    # ==================================================

    async def _gemini_stream_worker(
        self,
        state: ConversationState,
        instruction: str,
        version: int,
        task_id: str,
        queue: asyncio.Queue
    ):

        user_message_added = False

        response_text = ""

        # ----------------------------------------------
        # LATENCY TIMER
        # ----------------------------------------------

        request_start = time.perf_counter()

        first_token_time = None

        try:

            # ------------------------------------------
            # Add user message
            # ------------------------------------------

            state.conversation_history.append(

                {
                    "role": "user",

                    "content": instruction
                }

            )

            user_message_added = True

            # ------------------------------------------
            # Keep recent conversation
            # ------------------------------------------

            history = (
                state.conversation_history[-20:]
            )

            # ------------------------------------------
            # Build conversation prompt
            # ------------------------------------------

            conversation_text = ""

            for message in history:

                role = message["role"]

                content = message["content"]

                if role == "user":

                    conversation_text += (
                        f"User: {content}\n"
                    )

                else:

                    conversation_text += (
                        f"DataForge: {content}\n"
                    )

            prompt = f"""
You are DataForge, a helpful voice-native AI assistant.

Your job is to have a natural conversation with the user.

Rules:

- Speak naturally.
- Give direct answers.
- Keep normal answers concise enough for voice.
- If the user specifically asks for a long story,
  explanation or detailed answer, provide the requested length.
- Do not say "I received your instruction".
- Do not mention internal systems, APIs or models.
- Answer the user's latest request directly.

Conversation:

{conversation_text}

DataForge:
"""

            # ------------------------------------------
            # Gemini configuration
            # ------------------------------------------

            config = get_gemini_config()

            print()
            print("🚀 Starting Gemini streaming...")

            print(
                f"⏱️ Request started: "
                f"{request_start:.4f}"
            )

            # ------------------------------------------
            # GEMINI ASYNC STREAM
            # ------------------------------------------

            stream = (

                await gemini_client.aio.models.generate_content_stream(

                    model=GEMINI_MODEL,

                    contents=prompt,

                    config=config

                )

            )

            # ------------------------------------------
            # Receive Gemini chunks
            # ------------------------------------------

            async for chunk in stream:

                # --------------------------------------
                # IMPORTANT:
                # Ignore stale Gemini response
                # --------------------------------------

                if not state.is_current(
                    version
                ):

                    print(
                        "⚠️ Gemini stream became stale"
                    )

                    return

                chunk_text = (
                    getattr(
                        chunk,
                        "text",
                        None
                    )
                    or ""
                )

                if not chunk_text:

                    continue

                # --------------------------------------
                # FIRST TOKEN LATENCY
                # --------------------------------------

                if first_token_time is None:

                    first_token_time = (
                        time.perf_counter()
                    )

                    first_token_latency = (
                        first_token_time
                        -
                        request_start
                    )

                    print()
                    print(
                        "⚡ FIRST GEMINI TOKEN"
                    )

                    print(
                        f"⏱️ Time to first token: "
                        f"{first_token_latency:.3f}s"
                    )

                    print(
                        f"🤖 Model: "
                        f"{GEMINI_MODEL}"
                    )

                    print()

                response_text += chunk_text

                print(
                    "🧩 Gemini chunk:",
                    repr(chunk_text)
                )

                # --------------------------------------
                # Send text chunk to frontend
                # --------------------------------------

                queue.put_nowait(

                    {
                        "type": "text",

                        "text": chunk_text,

                        "task_id": task_id,

                        "version": version
                    }

                )

            # ------------------------------------------
            # TOTAL GEMINI TIME
            # ------------------------------------------

            total_time = (
                time.perf_counter()
                -
                request_start
            )

            print()
            print(
                "✅ Gemini streaming completed"
            )

            print(
                f"⏱️ Total Gemini time: "
                f"{total_time:.3f}s"
            )

            if first_token_time:

                print(
                    f"⚡ First token latency: "
                    f"{first_token_time - request_start:.3f}s"
                )

            print()

            # ------------------------------------------
            # Final stale check
            # ------------------------------------------

            if not state.is_current(
                version
            ):

                print(
                    "⚠️ Gemini response is stale"
                )

                return

            # ------------------------------------------
            # Empty response protection
            # ------------------------------------------

            if not response_text.strip():

                response_text = (
                    "Sorry, I couldn't generate "
                    "a response."
                )

            # ------------------------------------------
            # Save assistant response
            # ------------------------------------------

            state.conversation_history.append(

                {
                    "role": "assistant",

                    "content": response_text
                }

            )

            # ------------------------------------------
            # Send stream completion
            # ------------------------------------------

            queue.put_nowait(

                {
                    "type": "done",

                    "task_id": task_id,

                    "version": version
                }

            )

        except asyncio.CancelledError:

            print(
                f"🛑 Gemini task cancelled "
                f"version={version}"
            )

            # ------------------------------------------
            # Remove stale user message if possible
            # ------------------------------------------

            if user_message_added:

                if (
                    state.conversation_history
                    and
                    state.conversation_history[-1].get(
                        "role"
                    ) == "user"
                    and
                    state.conversation_history[-1].get(
                        "content"
                    ) == instruction
                ):

                    state.conversation_history.pop()

            # ------------------------------------------
            # Tell frontend stream was cancelled
            # ------------------------------------------

            queue.put_nowait(

                {
                    "type": "cancelled",

                    "task_id": task_id,

                    "version": version
                }

            )

            raise

        except Exception as error:

            print(
                "❌ Gemini streaming error:",
                error
            )

            queue.put_nowait(

                {
                    "type": "error",

                    "text": (
                        "Sorry, I encountered an error "
                        "while processing your request."
                    ),

                    "task_id": task_id,

                    "version": version
                }

            )

        finally:

            # ------------------------------------------
            # Tell stream consumer that worker finished
            # ------------------------------------------

            queue.put_nowait(None)


    # ==================================================
    # NON-STREAMING COMPATIBILITY METHOD
    # ==================================================

    async def process_instruction(
        self,
        conversation_id: str,
        instruction: str
    ):

        state = self.get_conversation(
            conversation_id
        )

        await self._cancel_current_task(
            state
        )

        state.new_instruction(
            instruction
        )

        version = state.response_version

        task_id = str(
            uuid.uuid4()
        )

        request_start = time.perf_counter()

        print(
            f"🧠 Processing instruction "
            f"version={version}"
        )

        try:

            state.conversation_history.append(

                {
                    "role": "user",

                    "content": instruction
                }

            )

            history = (
                state.conversation_history[-20:]
            )

            conversation_text = ""

            for message in history:

                if message["role"] == "user":

                    conversation_text += (
                        f"User: {message['content']}\n"
                    )

                else:

                    conversation_text += (
                        f"DataForge: {message['content']}\n"
                    )

            prompt = f"""
You are DataForge, a helpful voice-native AI assistant.

Speak naturally and answer the user's latest request
directly and concisely.

Conversation:

{conversation_text}

DataForge:
"""

            print(
                "🤖 Sending request to Gemini..."
            )

            # ------------------------------------------
            # Gemini configuration
            # ------------------------------------------

            config = get_gemini_config()

            response = (

                await gemini_client.aio.models.generate_content(

                    model=GEMINI_MODEL,

                    contents=prompt,

                    config=config

                )

            )

            total_time = (
                time.perf_counter()
                -
                request_start
            )

            print(
                f"⏱️ Gemini response time: "
                f"{total_time:.3f}s"
            )

            if not state.is_current(
                version
            ):

                return {

                    "status": "stale",

                    "task_id": task_id,

                    "version": version
                }

            response_text = (

                getattr(
                    response,
                    "text",
                    None
                )

                or

                "Sorry, I couldn't generate a response."

            )

            state.conversation_history.append(

                {
                    "role": "assistant",

                    "content": response_text
                }

            )

            print(
                "✅ Gemini response generated"
            )

            return {

                "status": "completed",

                "task_id": task_id,

                "version": version,

                "response": response_text
            }

        except asyncio.CancelledError:

            print(
                f"🛑 Task cancelled "
                f"version={version}"
            )

            return {

                "status": "cancelled",

                "task_id": task_id,

                "version": version
            }

        except Exception as error:

            print(
                "❌ Gemini error:",
                error
            )

            return {

                "status": "error",

                "task_id": task_id,

                "version": version,

                "response": (
                    "Sorry, I encountered an error "
                    "while processing your request."
                )

            }