"""
Voice Tool - Speech-to-text and text-to-speech for agents.
Gives agents the ability to process voice input and generate voice output.
"""

import base64
import time

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel
from app.integrations.voice.openai_voice import OpenAIWhisperSTT, OpenAITTS
from app.integrations.voice.base_voice import VoiceConfig


class VoiceTool(BaseTool):
    """
    Speech-to-text and text-to-speech capabilities.
    Configure via environment variables or tool config:
      OPENAI_API_KEY - For both Whisper (STT) and TTS
      Or use provider-specific keys in config.

    Operations:
    - transcribe: Convert audio to text using STT
    - synthesize: Convert text to audio using TTS
    - get_voices: List available TTS voices
    - get_languages: List supported STT languages
    - voice_preview: Preview a TTS voice
    """

    name = "voice"
    description = (
        "Process voice input and output. "
        "Use 'transcribe' to convert audio (base64 or URL) to text. "
        "Use 'synthesize' to convert text to speech and get audio. "
        "Use 'get_voices' to list available TTS voices. "
        "Use 'get_languages' to list supported STT languages. "
        "Requires OPENAI_API_KEY for OpenAI Whisper and TTS."
    )
    category = ToolCategory.COMMUNICATION
    risk_level = ToolRiskLevel.NORMAL

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'transcribe', 'synthesize', 'get_voices', 'get_languages', 'preview'",
                required=True,
                enum=[
                    "transcribe",
                    "synthesize",
                    "get_voices",
                    "get_languages",
                    "preview",
                ],
            ),
            "audio_data": ToolParameter(
                name="audio_data",
                type="string",
                description="Audio data - base64 encoded or URL to audio file (for transcribe)",
                required=False,
                default=None,
            ),
            "text": ToolParameter(
                name="text",
                type="string",
                description="Text to synthesize to speech (for synthesize)",
                required=False,
                default=None,
            ),
            "language": ToolParameter(
                name="language",
                type="string",
                description="Language code (e.g., 'en-US', 'es-ES') or 'auto' for detection",
                required=False,
                default="en-US",
            ),
            "voice_id": ToolParameter(
                name="voice_id",
                type="string",
                description="TTS voice ID: 'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'",
                required=False,
                default="alloy",
            ),
            "speed": ToolParameter(
                name="speed",
                type="number",
                description="Speech speed (0.25 to 4.0, default 1.0)",
                required=False,
                default=1.0,
            ),
            "prompt": ToolParameter(
                name="prompt",
                type="string",
                description="Optional prompt to guide transcription (context/hints)",
                required=False,
                default=None,
            ),
            "filter_profanity": ToolParameter(
                name="filter_profanity",
                type="boolean",
                description="Filter profanity from output",
                required=False,
                default=False,
            ),
        }

    def _validate_config(self) -> None:
        import os

        self.api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.default_voice = self.config.get("default_voice", "alloy")
        self.default_language = self.config.get("language", "en-US")
        self._stt_service = None
        self._tts_service = None

    def _get_stt_service(self) -> OpenAIWhisperSTT:
        """Get or create STT service"""
        if self._stt_service is None:
            config = VoiceConfig(api_key=self.api_key)
            self._stt_service = OpenAIWhisperSTT(config)
        return self._stt_service

    def _get_tts_service(self) -> OpenAITTS:
        """Get or create TTS service"""
        if self._tts_service is None:
            config = VoiceConfig(api_key=self.api_key, voice_id=self.default_voice)
            self._tts_service = OpenAITTS(config)
        return self._tts_service

    async def _transcribe(
        self, audio_data: str, language: str, prompt: str | None
    ) -> ToolResult:
        """Transcribe audio to text"""
        if not self.api_key:
            return ToolResult(
                success=False,
                error="OPENAI_API_KEY not configured. Set api_key in config or OPENAI_API_KEY env var.",
            )

        stt = self._get_stt_service()
        await stt.initialize()

        audio_bytes = None
        audio_url = None

        if audio_data.startswith("data:"):
            header, data = audio_data.split(",", 1)
            audio_bytes = base64.b64decode(data)
        elif audio_data.startswith("http://") or audio_data.startswith("https://"):
            audio_url = audio_data
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(audio_data, timeout=30)
                if response.status_code == 200:
                    audio_bytes = response.content
        else:
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception:
                return ToolResult(
                    success=False,
                    error="Invalid audio_data format. Provide base64, URL, or data URI.",
                )

        if not audio_bytes:
            return ToolResult(success=False, error="Failed to load audio data")

        lang = None if language == "auto" else language
        result = await stt.transcribe_audio(audio_bytes, lang, prompt)

        if not result.text:
            return ToolResult(
                success=False,
                error="Transcription failed or returned empty result",
            )

        return ToolResult(
            success=True,
            data={
                "text": result.text,
                "language": result.language,
                "duration_seconds": result.duration,
                "confidence": result.confidence,
            },
            stdout=f"Transcription: {result.text}\nLanguage: {result.language}\nDuration: {result.duration}s",
        )

    async def _synthesize(
        self, text: str, voice_id: str, speed: float, language: str
    ) -> ToolResult:
        """Synthesize text to speech"""
        if not self.api_key:
            return ToolResult(
                success=False,
                error="OPENAI_API_KEY not configured. Set api_key in config or OPENAI_API_KEY env var.",
            )

        if not text:
            return ToolResult(success=False, error="text is required for synthesize")

        tts = self._get_tts_service()
        await tts.initialize()

        voice = voice_id if voice_id else self.default_voice
        result = await tts.synthesize_speech(text, voice, language, speed)

        if not result.audio_data:
            return ToolResult(success=False, error="TTS synthesis failed")

        audio_b64 = base64.b64encode(result.audio_data).decode("utf-8")
        data_uri = f"data:audio/mp3;base64,{audio_b64}"

        return ToolResult(
            success=True,
            data={
                "audio_url": data_uri,
                "duration_seconds": result.duration,
                "format": result.format,
                "voice": voice,
            },
            stdout=f"Audio synthesized ({result.duration:.1f}s). Use audio_url for playback.",
        )

    async def _get_voices(self, language: str | None) -> ToolResult:
        """List available TTS voices"""
        if not self.api_key:
            return ToolResult(
                success=False,
                error="OPENAI_API_KEY not configured",
            )

        tts = self._get_tts_service()
        await tts.initialize()

        voices = await tts.get_available_voices(language)

        lines = ["Available TTS Voices:\n"]
        for v in voices:
            lines.append(f"- {v['id']}: {v['name']} ({v['gender']}, {v['language']})")

        return ToolResult(
            success=True,
            data={"voices": voices, "count": len(voices)},
            stdout="\n".join(lines),
        )

    async def _get_languages(self) -> ToolResult:
        """List supported STT languages"""
        if not self.api_key:
            return ToolResult(
                success=False,
                error="OPENAI_API_KEY not configured",
            )

        stt = self._get_stt_service()
        await stt.initialize()

        languages = await stt.get_supported_languages()

        lines = ["Supported Transcription Languages:\n"]
        for lang in languages[:15]:
            lines.append(f"- {lang['code']}: {lang['name']}")

        return ToolResult(
            success=True,
            data={"languages": languages, "count": len(languages)},
            stdout="\n".join(lines),
        )

    async def _preview_voice(self, voice_id: str) -> ToolResult:
        """Preview a TTS voice"""
        if not self.api_key:
            return ToolResult(
                success=False,
                error="OPENAI_API_KEY not configured",
            )

        tts = self._get_tts_service()
        await tts.initialize()

        voice = voice_id if voice_id else self.default_voice
        audio = await tts.get_voice_preview(voice)

        if not audio:
            return ToolResult(success=False, error="Failed to generate voice preview")

        audio_b64 = base64.b64encode(audio).decode("utf-8")
        data_uri = f"data:audio/mp3;base64,{audio_b64}"

        return ToolResult(
            success=True,
            data={
                "audio_url": data_uri,
                "voice": voice,
            },
            stdout=f"Voice preview for '{voice}' generated.",
        )

    async def execute(
        self,
        operation: str,
        audio_data: str | None = None,
        text: str | None = None,
        language: str = "en-US",
        voice_id: str | None = None,
        speed: float = 1.0,
        prompt: str | None = None,
        filter_profanity: bool = False,
    ) -> ToolResult:
        start_time = time.time()

        try:
            match operation:
                case "transcribe":
                    if not audio_data:
                        return ToolResult(
                            success=False,
                            error="audio_data is required for transcribe operation",
                        )
                    result = await self._transcribe(audio_data, language, prompt)

                case "synthesize":
                    result = await self._synthesize(
                        text or "", voice_id or self.default_voice, speed, language
                    )

                case "get_voices":
                    result = await self._get_voices(None)

                case "get_languages":
                    result = await self._get_languages()

                case "preview":
                    result = await self._preview_voice(voice_id or self.default_voice)

                case _:
                    result = ToolResult(
                        success=False, error=f"Unknown operation: {operation}"
                    )

            result.execution_time_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Voice operation failed: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
