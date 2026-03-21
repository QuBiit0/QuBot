"""
Voice Integration Package
Supports speech-to-text (STT) and text-to-speech (TTS) for voice mode
"""

from .base_voice import (
    BaseVoiceService,
    BaseSTTService,
    BaseTTSService,
    VoiceConfig,
    TranscriptionResult,
    SynthesisResult,
)

__all__ = [
    "BaseVoiceService",
    "BaseSTTService",
    "BaseTTSService",
    "VoiceConfig",
    "TranscriptionResult",
    "SynthesisResult",
]
