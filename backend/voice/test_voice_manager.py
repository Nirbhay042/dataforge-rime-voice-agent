import asyncio

from backend.voice.voice_manager import VoiceManager


async def fake_audio_task():
    try:
        print("Audio started...")

        # Simulate audio playing for 10 seconds
        await asyncio.sleep(10)

        print("Audio finished normally.")

    except asyncio.CancelledError:
        print("OLD AUDIO STOPPED!")

        # Re-raise cancellation so VoiceManager knows
        # the task was actually cancelled.
        raise


async def main():

    voice_manager = VoiceManager()

    conversation_id = "test-conversation"

    # Start simulated audio
    audio_task = asyncio.create_task(
        fake_audio_task()
    )

    # Register it with VoiceManager
    voice_manager.register(
        conversation_id,
        audio_task
    )

    # Let the audio run briefly
    await asyncio.sleep(2)

    print("User interrupted!")

    # Stop the current audio
    await voice_manager.stop_current(
        conversation_id
    )

    print("Interruption test completed.")


if __name__ == "__main__":
    asyncio.run(main())