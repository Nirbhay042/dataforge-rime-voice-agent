import asyncio
from typing import Dict, Optional


class VoiceManager:
    def __init__(self):
        self.current_audio_tasks: Dict[str, asyncio.Task] = {}

    def register(
        self,
        conversation_id: str,
        audio_task: asyncio.Task
    ):
        self.current_audio_tasks[conversation_id] = audio_task

    async def stop_current(self, conversation_id: str):
        audio_task: Optional[asyncio.Task] = (
            self.current_audio_tasks.get(conversation_id)
        )

        if audio_task and not audio_task.done():
            audio_task.cancel()

            try:
                await audio_task
            except asyncio.CancelledError:
                pass

        self.current_audio_tasks.pop(conversation_id, None)

    def has_active_audio(self, conversation_id: str) -> bool:
        audio_task = self.current_audio_tasks.get(conversation_id)

        return (
            audio_task is not None
            and not audio_task.done()
        )

    def get_current_audio_task(
        self,
        conversation_id: str
    ) -> Optional[asyncio.Task]:
        return self.current_audio_tasks.get(conversation_id)