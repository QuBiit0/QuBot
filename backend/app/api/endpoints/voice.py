"""
Voice API Endpoints
Speech-to-text and text-to-speech services
"""

from __future__ import annotations

import base64
import os
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response

from ...integrations.voice.openai_voice import OpenAIWhisperSTT, OpenAITTS
from ...integrations.voice.base_voice import VoiceConfig

router = APIRouter(prefix="/voice", tags=["voice"])


def get_api_key() -> str | None:
    """Get OpenAI API key from config or environment"""
    return os.getenv("OPENAI_API_KEY")


@router.get("/status")
async def voice_status():
    """Check voice service status"""
    api_key = get_api_key()
    return {
        "stt": {
            "provider": "openai_whisper",
            "available": bool(api_key),
            "configured": bool(api_key),
        },
        "tts": {
            "provider": "openai_tts",
            "available": bool(api_key),
            "configured": bool(api_key),
        },
    }


@router.get("/voices")
async def list_voices(language: str | None = Query(None)):
    """List available TTS voices"""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    config = VoiceConfig(api_key=api_key)
    tts = OpenAITTS(config)
    await tts.initialize()

    voices = await tts.get_available_voices(language)
    return {"voices": voices, "count": len(voices)}


@router.post("/voices/{voice_id}/preview")
async def voice_preview(voice_id: str):
    """Generate preview audio for a voice"""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    config = VoiceConfig(api_key=api_key)
    tts = OpenAITTS(config)
    await tts.initialize()

    audio = await tts.get_voice_preview(voice_id)
    if not audio:
        raise HTTPException(status_code=500, detail="Failed to generate voice preview")

    return Response(content=audio, media_type="audio/mp3")


@router.get("/languages")
async def list_languages():
    """List supported STT languages"""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    config = VoiceConfig(api_key=api_key)
    stt = OpenAIWhisperSTT(config)
    await stt.initialize()

    languages = await stt.get_supported_languages()
    return {"languages": languages, "count": len(languages)}


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Query(None),
    prompt: str | None = Query(None),
):
    """Transcribe audio file to text"""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    audio_data = await file.read()

    config = VoiceConfig(api_key=api_key)
    stt = OpenAIWhisperSTT(config)
    await stt.initialize()

    result = await stt.transcribe_audio(audio_data, language, prompt)

    return {
        "text": result.text,
        "language": result.language,
        "duration_seconds": result.duration,
        "confidence": result.confidence,
        "words": result.words,
    }


@router.post("/transcribe/base64")
async def transcribe_base64(
    audio_data: str = Form(...),
    language: str | None = Form(None),
    prompt: str | None = Form(None),
):
    """Transcribe base64-encoded audio to text"""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    try:
        audio_bytes = base64.b64decode(audio_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 audio data")

    config = VoiceConfig(api_key=api_key)
    stt = OpenAIWhisperSTT(config)
    await stt.initialize()

    result = await stt.transcribe_audio(audio_bytes, language, prompt)

    return {
        "text": result.text,
        "language": result.language,
        "duration_seconds": result.duration,
        "confidence": result.confidence,
    }


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    voice: str = Form("alloy"),
    language: str | None = Form(None),
    speed: float = Form(1.0),
):
    """Synthesize text to speech"""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    config = VoiceConfig(api_key=api_key, voice_id=voice)
    tts = OpenAITTS(config)
    await tts.initialize()

    result = await tts.synthesize_speech(text, voice, language, speed)

    if not result.audio_data:
        raise HTTPException(status_code=500, detail="TTS synthesis failed")

    audio_b64 = base64.b64encode(result.audio_data).decode("utf-8")
    data_uri = f"data:audio/mp3;base64,{audio_b64}"

    return {
        "audio_url": data_uri,
        "duration_seconds": result.duration,
        "format": result.format,
        "voice": voice,
    }


@router.get("/synthesize/stream/{text}")
async def synthesize_stream(
    text: str,
    voice: str = Query("alloy"),
):
    """Stream synthesize text to speech (returns audio bytes)"""
    import httpx

    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "tts-1",
                    "input": text[:4096],
                    "voice": voice,
                    "response_format": "mp3",
                },
                timeout=60,
            )

            if response.status_code == 200:
                return Response(content=response.content, media_type="audio/mp3")

        raise HTTPException(status_code=500, detail="TTS synthesis failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {str(e)}")


@router.get("/schemas")
async def voice_schemas():
    """Get voice service configuration schemas"""
    return {
        "schemas": {
            "stt": {
                "provider": "openai_whisper",
                "model": "whisper-1",
                "features": ["transcription", "timestamping", "language_detection"],
            },
            "tts": {
                "provider": "openai_tts",
                "model": "tts-1",
                "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "features": ["streaming", "speed_control"],
            },
        }
    }
