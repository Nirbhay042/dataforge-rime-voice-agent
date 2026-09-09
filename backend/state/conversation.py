from dataclasses import dataclass
from typing import Optional
import asyncio


@dataclass
class ConversationState:
    conversation_id: str

    current_task_id: Optional[str] = None
    latest_user_instruction: Optional[str] = None

    task: Optional[asyncio.Task] = None

    response_version: int = 0

    def new_instruction(self, instruction: str):
        """
        Store the latest user instruction.

        Every new instruction increases the response version.
        Older results can then be identified as stale.
        """
        self.latest_user_instruction = instruction
        self.response_version += 1

    def is_current(self, version: int) -> bool:
        """
        Check whether a result belongs to the latest instruction.
        """
        return version == self.response_version