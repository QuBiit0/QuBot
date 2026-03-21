"use client";

import { useState, useRef, useEffect } from "react";
import {
  Mic,
  MicOff,
  Volume2,
  Settings,
  Play,
  Pause,
  RefreshCw,
  Check,
  X,
} from "lucide-react";

interface VoiceConfig {
  stt_available: boolean;
  tts_available: boolean;
  configured: boolean;
}

interface Voice {
  id: string;
  name: string;
  gender: string;
  language: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function VoicePage() {
  const [darkMode, setDarkMode] = useState(true);
  const [voiceConfig, setVoiceConfig] = useState<VoiceConfig | null>(null);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState("alloy");
  const [isRecording, setIsRecording] = useState(false);
  const [transcribedText, setTranscribedText] = useState("");
  const [synthesizedText, setSynthesizedText] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    loadVoiceStatus();
    loadVoices();
  }, []);

  const loadVoiceStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/voice/status`);
      if (res.ok) {
        const data = await res.json();
        setVoiceConfig({
          stt_available: data.stt?.available || false,
          tts_available: data.tts?.available || false,
          configured: data.stt?.configured || false,
        });
      }
    } catch {
      console.error("Failed to load voice status");
    }
  };

  const loadVoices = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/voice/voices`);
      if (res.ok) {
        const data = await res.json();
        setVoices(data.voices || []);
      }
    } catch {
      console.error("Failed to load voices");
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await transcribeAudio(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Failed to start recording:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (blob: Blob) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", blob, "audio.webm");

      const res = await fetch(`${API_BASE_URL}/api/v1/voice/transcribe`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setTranscribedText(data.text || "");
      }
    } catch {
      console.error("Failed to transcribe");
    }
    setLoading(false);
  };

  const synthesizeText = async () => {
    if (!synthesizedText) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/voice/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: synthesizedText,
          voice: selectedVoice,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setAudioUrl(data.audio_url);
      }
    } catch {
      console.error("Failed to synthesize");
    }
    setLoading(false);
  };

  const playAudio = () => {
    if (audioUrl && audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const voicesByGender = {
    male: voices.filter((v) => v.gender === "male"),
    female: voices.filter((v) => v.gender === "female"),
    neutral: voices.filter((v) => v.gender === "neutral"),
  };

  return (
    <div className="flex h-screen" style={{ backgroundColor: darkMode ? "#0d1117" : "#f6f8fa" }}>
      <div className="flex-1 flex flex-col">
        <header
          className="border-b px-6 py-4 flex items-center justify-between"
          style={{
            backgroundColor: darkMode ? "#161b22" : "#ffffff",
            borderColor: darkMode ? "#30363d" : "#d0d7de",
          }}
        >
          <div className="flex items-center gap-4">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #6366f1, #ec4899)" }}
            >
              <Mic className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
              Voice Mode
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: darkMode ? "#8b949e" : "#57606a" }}
            >
              <Settings className="w-4 h-4" />
            </button>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
              style={{
                backgroundColor: darkMode ? "rgba(255,255,255,0.05)" : "#eaeef2",
                color: darkMode ? "#e6edf3" : "#1e293b",
              }}
            >
              {darkMode ? "Light" : "Dark"}
            </button>
          </div>
        </header>

        <div className="flex-1 p-6 overflow-auto">
          <div className="max-w-4xl mx-auto space-y-6">
            {!voiceConfig?.configured ? (
              <div
                className="p-8 rounded-2xl text-center"
                style={{
                  backgroundColor: darkMode ? "#161b22" : "#ffffff",
                  border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                }}
              >
                <div
                  className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
                  style={{ backgroundColor: "rgba(99,102,241,0.1)" }}
                >
                  <Volume2 className="w-8 h-8" style={{ color: "#6366f1" }} />
                </div>
                <h2 className="text-xl font-semibold mb-2" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                  Voice Services
                </h2>
                <p className="text-sm mb-4" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Configure your OpenAI API key to enable speech-to-text and text-to-speech features
                </p>
                <div
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg"
                  style={{ backgroundColor: "rgba(248,81,73,0.1)" }}
                >
                  <X className="w-4 h-4" style={{ color: "#f85149" }} />
                  <span className="text-sm" style={{ color: "#f85149" }}>
                    OPENAI_API_KEY not configured
                  </span>
                </div>
              </div>
            ) : (
              <>
                <div
                  className="p-6 rounded-xl"
                  style={{
                    backgroundColor: darkMode ? "#161b22" : "#ffffff",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                >
                  <h3 className="text-lg font-semibold mb-4" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                    Speech to Text
                  </h3>

                  <div className="flex items-center justify-center mb-6">
                    <button
                      onClick={isRecording ? stopRecording : startRecording}
                      disabled={loading}
                      className={`w-24 h-24 rounded-full flex items-center justify-center transition-all ${
                        isRecording ? "animate-pulse" : ""
                      }`}
                      style={{
                        backgroundColor: isRecording ? "#ef4444" : "#6366f1",
                        boxShadow: isRecording
                          ? "0 0 30px rgba(239,68,68,0.5)"
                          : "0 0 30px rgba(99,102,241,0.3)",
                      }}
                    >
                      {loading ? (
                        <RefreshCw className="w-8 h-8 text-white animate-spin" />
                      ) : isRecording ? (
                        <MicOff className="w-8 h-8 text-white" />
                      ) : (
                        <Mic className="w-8 h-8 text-white" />
                      )}
                    </button>
                  </div>

                  <p className="text-center text-sm mb-4" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                    {isRecording ? "Recording... Click to stop" : "Click to start recording"}
                  </p>

                  {transcribedText && (
                    <div
                      className="p-4 rounded-lg"
                      style={{
                        backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                        border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                      }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                          Transcription
                        </span>
                        <button
                          onClick={() => setSynthesizedText(transcribedText)}
                          className="text-xs px-2 py-1 rounded"
                          style={{ backgroundColor: "rgba(99,102,241,0.1)", color: "#6366f1" }}
                        >
                          Use for TTS
                        </button>
                      </div>
                      <p style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>{transcribedText}</p>
                    </div>
                  )}
                </div>

                <div
                  className="p-6 rounded-xl"
                  style={{
                    backgroundColor: darkMode ? "#161b22" : "#ffffff",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                >
                  <h3 className="text-lg font-semibold mb-4" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                    Text to Speech
                  </h3>

                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-2" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                      Voice
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {["alloy", "echo", "fable", "onyx", "nova", "shimmer"].map((voice) => (
                        <button
                          key={voice}
                          onClick={() => setSelectedVoice(voice)}
                          className="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                          style={{
                            backgroundColor:
                              selectedVoice === voice
                                ? "#6366f1"
                                : darkMode
                                ? "rgba(255,255,255,0.05)"
                                : "#f6f8fa",
                            color: selectedVoice === voice ? "#ffffff" : darkMode ? "#e6edf3" : "#1e293b",
                            border: `1px solid ${selectedVoice === voice ? "#6366f1" : darkMode ? "#30363d" : "#d0d7de"}`,
                          }}
                        >
                          {voice}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-2" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                      Text to Synthesize
                    </label>
                    <textarea
                      value={synthesizedText}
                      onChange={(e) => setSynthesizedText(e.target.value)}
                      placeholder="Enter text to convert to speech..."
                      rows={4}
                      className="w-full px-4 py-3 rounded-lg resize-none"
                      style={{
                        backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                        color: darkMode ? "#e6edf3" : "#1e293b",
                        border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                      }}
                    />
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={synthesizeText}
                      disabled={loading || !synthesizedText}
                      className="flex-1 px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                      style={{
                        backgroundColor: synthesizedText ? "#6366f1" : "rgba(99,102,241,0.3)",
                        color: "#ffffff",
                      }}
                    >
                      <Volume2 className="w-4 h-4" />
                      Generate Audio
                    </button>

                    {audioUrl && (
                      <button
                        onClick={isPlaying ? pauseAudio : playAudio}
                        className="px-4 py-2 rounded-lg font-medium transition-colors"
                        style={{
                          backgroundColor: darkMode ? "rgba(255,255,255,0.05)" : "#f6f8fa",
                          color: darkMode ? "#e6edf3" : "#1e293b",
                        }}
                      >
                        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      </button>
                    )}
                  </div>

                  {audioUrl && (
                    <audio
                      ref={audioRef}
                      src={audioUrl}
                      onEnded={() => setIsPlaying(false)}
                      className="hidden"
                    />
                  )}
                </div>

                <div
                  className="p-6 rounded-xl"
                  style={{
                    backgroundColor: darkMode ? "#161b22" : "#ffffff",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                >
                  <h3 className="text-lg font-semibold mb-4" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                    Available Voices
                  </h3>
                  <div className="space-y-4">
                    {Object.entries(voicesByGender).map(([gender, voiceList]) =>
                      voiceList.length > 0 ? (
                        <div key={gender}>
                          <h4 className="text-sm font-medium mb-2 capitalize" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                            {gender}
                          </h4>
                          <div className="grid grid-cols-2 gap-2">
                            {voiceList.map((voice) => (
                              <div
                                key={voice.id}
                                className="p-3 rounded-lg flex items-center justify-between"
                                style={{
                                  backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                                  border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                                }}
                              >
                                <div>
                                  <div className="font-medium text-sm" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                                    {voice.name}
                                  </div>
                                  <div className="text-xs" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                                    {voice.language}
                                  </div>
                                </div>
                                {selectedVoice === voice.id && (
                                  <Check className="w-4 h-4" style={{ color: "#6366f1" }} />
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {showSettings && (
        <div
          className="w-80 border-l p-6 overflow-auto"
          style={{
            backgroundColor: darkMode ? "#161b22" : "#ffffff",
            borderColor: darkMode ? "#30363d" : "#d0d7de",
          }}
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
              Voice Settings
            </h3>
            <button
              onClick={() => setShowSettings(false)}
              className="p-1 rounded hover:bg-white/5"
              style={{ color: darkMode ? "#8b949e" : "#57606a" }}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4">
            <div
              className="p-4 rounded-lg"
              style={{
                backgroundColor: darkMode ? "#21262d" : "#f6f8fa",
                border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <Mic className="w-4 h-4" style={{ color: "#6366f1" }} />
                <span className="font-medium" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                  Speech to Text
                </span>
              </div>
              <div
                className="text-xs px-2 py-1 rounded inline-block"
                style={{
                  backgroundColor: voiceConfig?.stt_available
                    ? "rgba(63,185,80,0.2)"
                    : "rgba(248,81,73,0.2)",
                  color: voiceConfig?.stt_available ? "#3fb950" : "#f85149",
                }}
              >
                {voiceConfig?.stt_available ? "Available" : "Not Available"}
              </div>
            </div>

            <div
              className="p-4 rounded-lg"
              style={{
                backgroundColor: darkMode ? "#21262d" : "#f6f8fa",
                border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <Volume2 className="w-4 h-4" style={{ color: "#ec4899" }} />
                <span className="font-medium" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                  Text to Speech
                </span>
              </div>
              <div
                className="text-xs px-2 py-1 rounded inline-block"
                style={{
                  backgroundColor: voiceConfig?.tts_available
                    ? "rgba(63,185,80,0.2)"
                    : "rgba(248,81,73,0.2)",
                  color: voiceConfig?.tts_available ? "#3fb950" : "#f85149",
                }}
              >
                {voiceConfig?.tts_available ? "Available" : "Not Available"}
              </div>
            </div>

            <div className="pt-4 border-t" style={{ borderColor: darkMode ? "#30363d" : "#d0d7de" }}>
              <p className="text-xs" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                Voice services use OpenAI Whisper for transcription and OpenAI TTS for speech synthesis.
                Set OPENAI_API_KEY in your environment or settings to enable.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
