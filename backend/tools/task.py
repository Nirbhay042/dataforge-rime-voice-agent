import asyncio
import uuid
from typing import Dict, Optional


class TaskManager:

    def __init__(self):
        self.current_tasks: Dict[str, asyncio.Task] = {}
        self.current_task_ids: Dict[str, str] = {}

    def create_task_id(self) -> str:
        return str(uuid.uuid4())

    async def cancel_current(self, conversation_id: str):
        """
        Cancel the currently running task for a conversation.
        """

        current_task: Optional[asyncio.Task] = (
            self.current_tasks.get(conversation_id)
        )

        if current_task and not current_task.done():

            current_task.cancel()

            try:
                await current_task

            except asyncio.CancelledError:
                pass

        self.current_tasks.pop(conversation_id, None)
        self.current_task_ids.pop(conversation_id, None)

    def register(
        self,
        conversation_id: str,
        task: asyncio.Task,
        task_id: str
    ):
        """
        Register a task for a specific conversation.
        """

        self.current_tasks[conversation_id] = task
        self.current_task_ids[conversation_id] = task_id

    def get_current_task_id(
        self,
        conversation_id: str
    ) -> Optional[str]:

        return self.current_task_ids.get(conversation_id)