"""
Base Voice Service - Abstract interfaces for STT and TTS
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Literal


@dataclass
class VoiceConfig:
    """Configuration for voice services"""

    provider: Literal["openai", "elevenlabs", "google", "aws", "azure"] = "openai"
    api_key: str | None = None
    api_secret: str | None = None
    region: str = "us-east-1"
    language: str = "en-US"
    model: str = "whisper-1"
    voice_id: str = "alloy"
    response_format: str = "json"
    speed: float = 1.0
    temperature: float = 0.0


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription"""

    text: str
    language: str | None = None
    duration: float | None = None
    confidence: float | None = None
    words: list[dict] = field(default_factory=list)
    segments: list[dict] = field(default_factory=list)


@dataclass
class SynthesisResult:
    """Result of text-to-speech synthesis"""

    audio_data: bytes | None = None
    audio_url: str | None = None
    duration: float | None = None
    sample_rate: int = 24000
    format: str = "mp3"


@dataclass
class VoiceSession:
    """Active voice session"""

    session_id: str
    user_id: str | None = None
    agent_id: str | None = None
    start_time: float | None = None
    language: str = "en-US"
    mode: Literal["full_duplex", "push_to_talk", "voice_activity"] = "push_to_talk"
    active: bool = True


class BaseVoiceService(ABC):
    """Base class for voice services"""

    def __init__(self, config: VoiceConfig | None = None):
        self.config = config or VoiceConfig()

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the voice service"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is healthy"""
        pass


class BaseSTTService(BaseVoiceService):
    """Base class for speech-to-text services"""

    @abstractmethod
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str | None = None,
        prompt: str | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (WAV, MP3, OGG, etc.)
            language: BCP-47 language code (e.g., 'en-US')
            prompt: Optional prompt to guide transcription

        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        language: str | None = None,
    ) -> AsyncGenerator[TranscriptionResult, None]:
        """
        Stream transcription for real-time processing.

        Args:
            audio_stream: Async generator of audio chunks
            language: BCP-47 language code

        Yields:
            TranscriptionResult objects as audio is processed
        """
        pass

    @abstractmethod
    async def get_supported_languages(self) -> list[dict]:
        """Get list of supported languages with codes and names"""
        pass


class BaseTTSService(BaseVoiceService):
    """Base class for text-to-speech services"""

    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str | None = None,
        language: str | None = None,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            voice_id: Voice identifier (provider-specific)
            language: BCP-47 language code
            speed: Speech speed (0.5 - 2.0)

        Returns:
            SynthesisResult with audio data or URL
        """
        pass

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        voice_id: str | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesis for real-time playback.

        Args:
            text: Text to synthesize
            voice_id: Voice identifier

        Yields:
            Audio chunks as they are generated
        """
        pass

    @abstractmethod
    async def get_available_voices(self, language: str | None = None) -> list[dict]:
        """
        Get list of available voices.

        Args:
            language: Filter by language (optional)

        Returns:
            List of voice objects with id, name, language, gender
        """
        pass

    @abstractmethod
    async def get_voice_preview(
        self, voice_id: str, text: str = "Hello, this is a voice preview."
    ) -> bytes:
        """
        Get a short audio preview of a voice.

        Args:
            voice_id: Voice identifier
            text: Preview text

        Returns:
            Audio bytes of the preview
        """
        pass
