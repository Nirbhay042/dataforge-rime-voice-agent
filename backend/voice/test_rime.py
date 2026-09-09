import asyncio

from backend.voice.rime_tts import RimeTTS


async def main():

    rime = RimeTTS()

    audio = await rime.synthesize(
        "Hello! This is the DataForge voice agent powered by Rime."
    )

    with open("rime_test.webm", "wb") as f:
        f.write(audio)

    print("Rime TTS successful!")
    print(f"Audio bytes received: {len(audio)}")


if __name__ == "__main__":
    asyncio.run(main())