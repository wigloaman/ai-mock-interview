import asyncio

import edge_tts
from django.conf import settings

from interview.ai import get_client

MAX_SPEECH_CHARS = 1000


def synthesize_speech(text):
    """Return MP3 audio of the text spoken by the configured neural voice (edge-tts, free)."""

    async def collect_audio():
        audio = bytearray()
        async for chunk in edge_tts.Communicate(text[:MAX_SPEECH_CHARS], settings.TTS_VOICE).stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        return bytes(audio)

    return asyncio.run(collect_audio())


def transcribe_audio(audio_file):
    """Return the text spoken in an uploaded audio file (Groq Whisper)."""
    transcription = get_client().audio.transcriptions.create(
        file=(audio_file.name, audio_file.read()),
        model=settings.STT_MODEL,
        language="en",
    )
    return transcription.text.strip()
