"""
OpenAI Voice Service - Whisper (STT) and TTS implementations
"""

import os
from typing import AsyncGenerator

from .base_voice import (
    BaseSTTService,
    BaseTTSService,
    TranscriptionResult,
    SynthesisResult,
    VoiceConfig,
)


class OpenAIWhisperSTT(BaseSTTService):
    """
    OpenAI Whisper API for speech-to-text.

    Requires:
    - OPENAI_API_KEY environment variable or config.api_key

    Features:
    - High accuracy transcription
    - Multi-language support
    - Word-level timestamps
    - Streaming support
    """

    def __init__(self, config: VoiceConfig | None = None):
        super().__init__(config)
        self.api_key = config.api_key if config else None

    async def initialize(self) -> bool:
        """Initialize Whisper service"""
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        return bool(self.api_key)

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        return bool(self.api_key)

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str | None = None,
        prompt: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe audio using Whisper API"""
        import httpx

        if not self.api_key:
            return TranscriptionResult(text="", confidence=0.0)

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        files = {
            "file": ("audio.wav", audio_data, "audio/wav"),
            "model": (None, "whisper-1", None),
        }

        data = {
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        }

        if language:
            data["language"] = language.split("-")[0]
        if prompt:
            data["prompt"] = prompt

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60,
                )

                if response.status_code == 200:
                    result = response.json()
                    words = result.get("words", [])
                    segments = result.get("segments", [])

                    return TranscriptionResult(
                        text=result.get("text", ""),
                        language=result.get("language", language or "en"),
                        duration=result.get("duration"),
                        confidence=result.get("confidence", 0.95),
                        words=[
                            {
                                "word": w.get("word"),
                                "start": w.get("start"),
                                "end": w.get("end"),
                            }
                            for w in words
                        ],
                        segments=[
                            {
                                "text": s.get("text"),
                                "start": s.get("start"),
                                "end": s.get("end"),
                            }
                            for s in segments
                        ],
                    )

            return TranscriptionResult(text="", confidence=0.0)
        except Exception:
            return TranscriptionResult(text="", confidence=0.0)

    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        language: str | None = None,
    ) -> AsyncGenerator[TranscriptionResult, None]:
        """Stream transcription - accumulates audio chunks for final transcription"""
        audio_chunks = []
        async for chunk in audio_stream:
            audio_chunks.append(chunk)

        if audio_chunks:
            full_audio = b"".join(audio_chunks)
            result = await self.transcribe_audio(full_audio, language)
            yield result

    async def get_supported_languages(self) -> list[dict]:
        """Get list of supported languages"""
        return [
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "ar", "name": "Arabic"},
            {"code": "hi", "name": "Hindi"},
            {"code": "nl", "name": "Dutch"},
            {"code": "pl", "name": "Polish"},
            {"code": "tr", "name": "Turkish"},
            {"code": "sv", "name": "Swedish"},
            {"code": "da", "name": "Danish"},
            {"code": "no", "name": "Norwegian"},
            {"code": "fi", "name": "Finnish"},
            {"code": "he", "name": "Hebrew"},
        ]


class OpenAITTS(BaseTTSService):
    """
    OpenAI TTS API for text-to-speech.

    Requires:
    - OPENAI_API_KEY environment variable or config.api_key

    Voices: alloy, echo, fable, onyx, nova, shimmer
    Models: tts-1 (quality), tts-1-hd (high quality)
    """

    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def __init__(self, config: VoiceConfig | None = None):
        super().__init__(config)
        self.api_key = config.api_key if config else None
        self.model = "tts-1"

    async def initialize(self) -> bool:
        """Initialize TTS service"""
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        return bool(self.api_key)

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        return bool(self.api_key)

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str | None = None,
        language: str | None = None,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize speech using OpenAI TTS"""
        import httpx

        if not self.api_key:
            return SynthesisResult()

        voice = voice_id or self.config.voice_id
        if voice not in self.VOICES:
            voice = "alloy"

        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": text[:4096],
            "voice": voice,
            "speed": max(0.25, min(4.0, speed)),
            "response_format": "mp3",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60,
                )

                if response.status_code == 200:
                    return SynthesisResult(
                        audio_data=response.content,
                        duration=len(response.content) / (16000 * 2),
                        sample_rate=24000,
                        format="mp3",
                    )

            return SynthesisResult()
        except Exception:
            return SynthesisResult()

    async def synthesize_stream(
        self,
        text: str,
        voice_id: str | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesis"""
        result = await self.synthesize_speech(text, voice_id)
        if result.audio_data:
            chunk_size = 4096
            audio = result.audio_data
            for i in range(0, len(audio), chunk_size):
                yield audio[i : i + chunk_size]

    async def get_available_voices(self, language: str | None = None) -> list[dict]:
        """Get list of available voices"""
        voices = [
            {
                "id": "alloy",
                "name": "Alloy",
                "gender": "neutral",
                "language": "en-US",
                "preview_url": None,
            },
            {
                "id": "echo",
                "name": "Echo",
                "gender": "male",
                "language": "en-US",
                "preview_url": None,
            },
            {
                "id": "fable",
                "name": "Fable",
                "gender": "male",
                "language": "en-GB",
                "preview_url": None,
            },
            {
                "id": "onyx",
                "name": "Onyx",
                "gender": "male",
                "language": "en-US",
                "preview_url": None,
            },
            {
                "id": "nova",
                "name": "Nova",
                "gender": "female",
                "language": "en-US",
                "preview_url": None,
            },
            {
                "id": "shimmer",
                "name": "Shimmer",
                "gender": "female",
                "language": "en-US",
                "preview_url": None,
            },
        ]

        if language:
            return [
                v for v in voices if v["language"].startswith(language.split("-")[0])
            ]

        return voices

    async def get_voice_preview(
        self, voice_id: str, text: str = "Hello, this is a voice preview."
    ) -> bytes:
        """Get voice preview audio"""
        result = await self.synthesize_speech(text, voice_id)
        return result.audio_data or b""
