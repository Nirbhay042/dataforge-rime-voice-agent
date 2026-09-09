import os

from typing import AsyncGenerator

import httpx

from dotenv import load_dotenv

load_dotenv()


class RimeTTS:

    def __init__(self):
        self.api_key = os.getenv("RIME_API_KEY")

        if not self.api_key:
            raise RuntimeError("RIME_API_KEY is not set.")

        self.url = "https://users.rime.ai/v1/rime-tts"

    def _headers(self):
        return {
            "Accept": "audio/webm;codecs=opus",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, text: str):
        return {
            "text": text,
            "modelId": "mistv3",
            "speaker": "cove",
            "lang": "eng",
            "samplingRate": 24000,
        }

    async def synthesize(self, text: str) -> bytes:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.url,
                headers=self._headers(),
                json=self._payload(text),
            )

            response.raise_for_status()

            return response.content

    async def stream(self, text: str) -> AsyncGenerator[bytes, None]:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                self.url,
                headers=self._headers(),
                json=self._payload(text),
            ) as response:

                response.raise_for_status()

                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk