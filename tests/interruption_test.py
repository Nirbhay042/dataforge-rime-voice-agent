import asyncio

import pytest

from backend.agent.orchestrator import AgentOrchestrator


@pytest.mark.asyncio
async def test_interruption_prevents_stale_result():

    orchestrator = AgentOrchestrator()

    conversation_id = "test-conversation"

    # Start the first request
    first_task = asyncio.create_task(
        orchestrator.process_instruction(
            conversation_id,
            "Tell me about Delhi"
        )
    )

    # Give the first task some time to start
    await asyncio.sleep(0.2)

    # User interrupts with a new request
    second_result = await orchestrator.process_instruction(
        conversation_id,
        "Tell me about Mumbai"
    )

    # The first request should be cancelled
    first_result = await first_task

    # New request must complete
    assert second_result["status"] == "completed"

    # Final response must contain the latest instruction
    assert "Mumbai" in second_result["response"]

    # Old request must not complete normally
    assert first_result["status"] == "cancelled"

@pytest.mark.asyncio
async def test_multiple_conversations_are_independent():

    orchestrator = AgentOrchestrator()

    # Conversation A starts
    task_a = asyncio.create_task(
        orchestrator.process_instruction(
            "conversation-a",
            "Tell me about Delhi"
        )
    )

    # Conversation B starts
    task_b = asyncio.create_task(
        orchestrator.process_instruction(
            "conversation-b",
            "Tell me about Mumbai"
        )
    )

    result_a = await task_a
    result_b = await task_b

    # Both conversations should complete
    assert result_a["status"] == "completed"
    assert result_b["status"] == "completed"

    # Each conversation should receive its own response
    assert "Delhi" in result_a["response"]
    assert "Mumbai" in result_b["response"]

    # Each task should have a unique ID
    assert result_a["task_id"] != result_b["task_id"]


@pytest.mark.asyncio
async def test_voice_interruption_cancels_old_audio():
    orchestrator = AgentOrchestrator()

    conversation_id = "voice-interruption-test"

    first_task = asyncio.create_task(
        orchestrator.process_instruction(
            conversation_id,
            "Tell me a long story about the DataForge project."
        )
    )

    # Give the first task time to start processing
    await asyncio.sleep(3.5)

    # New instruction interrupts the previous one
    second_task = asyncio.create_task(
        orchestrator.process_instruction(
            conversation_id,
            "Stop. Give me only a short greeting."
        )
    )

    first_result = await first_task
    second_result = await second_task

    assert second_result["status"] == "completed"

    assert (
        "short greeting"
        in second_result["response"]
    )

    assert first_result["status"] in [
        "cancelled",
        "stale"
    ]    