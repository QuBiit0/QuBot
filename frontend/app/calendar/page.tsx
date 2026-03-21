"use client";

import { useState, useEffect } from "react";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
  Clock,
  MapPin,
  Users,
  Settings,
  RefreshCw,
  ExternalLink,
  Trash2,
  Edit2,
  Check,
  X,
} from "lucide-react";

interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  location?: string;
  start_time: string;
  end_time: string;
  attendees?: string[];
  organizer?: string;
  status: string;
  html_link?: string;
}

interface CalendarConfig {
  google: { configured: boolean; client_id_set: boolean };
  outlook: { configured: boolean; client_id_set: boolean };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CalendarPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [provider, setProvider] = useState<"google" | "outlook">("google");
  const [calendarConfig, setCalendarConfig] = useState<CalendarConfig | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const [newEvent, setNewEvent] = useState({
    summary: "",
    description: "",
    location: "",
    start_date: "",
    start_time: "",
    end_date: "",
    end_time: "",
    attendees: "",
  });

  useEffect(() => {
    loadCalendarConfig();
    const saved = localStorage.getItem("calendar_token");
    if (saved) setToken(saved);
  }, []);

  const loadCalendarConfig = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/calendar/status`);
      if (res.ok) {
        const data = await res.json();
        setCalendarConfig(data);
      }
    } catch {
      console.error("Failed to load calendar config");
    }
  };

  const connectGoogle = () => {
    window.location.href = `${API_BASE_URL}/api/v1/calendar/google/authorize`;
  };

  const connectOutlook = () => {
    window.location.href = `${API_BASE_URL}/api/v1/calendar/outlook/authorize`;
  };

  const fetchEvents = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/calendar/events?provider=${provider}&max_results=50`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch {
      console.error("Failed to fetch events");
    }
    setLoading(false);
  };

  useEffect(() => {
    if (token) fetchEvents();
  }, [token, provider]);

  const handleCreateEvent = async () => {
    if (!token || !newEvent.summary || !newEvent.start_date || !newEvent.end_date) return;

    const start = new Date(`${newEvent.start_date}T${newEvent.start_time || "00:00"}`);
    const end = new Date(`${newEvent.end_date}T${newEvent.end_time || "00:00"}`);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/calendar/events`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          provider,
          summary: newEvent.summary,
          description: newEvent.description,
          location: newEvent.location,
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          attendees: newEvent.attendees ? newEvent.attendees.split(",").map((e) => e.trim()) : [],
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        }),
      });

      if (res.ok) {
        setShowCreateModal(false);
        setNewEvent({
          summary: "",
          description: "",
          location: "",
          start_date: "",
          start_time: "",
          end_date: "",
          end_time: "",
          attendees: "",
        });
        fetchEvents();
      }
    } catch {
      console.error("Failed to create event");
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    if (!token) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/calendar/events/${eventId}?provider=${provider}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        setSelectedEvent(null);
        fetchEvents();
      }
    } catch {
      console.error("Failed to delete event");
    }
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days = [];
    for (let i = 0; i < firstDay.getDay(); i++) {
      days.push(new Date(year, month, -i));
    }
    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i));
    }
    for (let i = 1; days.length < 42; i++) {
      days.push(new Date(year, month + 1, i));
    }
    return days;
  };

  const getEventsForDay = (day: Date) => {
    return events.filter((event) => {
      const eventDate = new Date(event.start_time);
      return (
        eventDate.getDate() === day.getDate() &&
        eventDate.getMonth() === day.getMonth() &&
        eventDate.getFullYear() === day.getFullYear()
      );
    });
  };

  const isToday = (day: Date) => {
    const today = new Date();
    return (
      day.getDate() === today.getDate() &&
      day.getMonth() === today.getMonth() &&
      day.getFullYear() === today.getFullYear()
    );
  };

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];

  const days = getDaysInMonth(currentDate);

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
            <Calendar className="w-6 h-6" style={{ color: "#6366f1" }} />
            <h1 className="text-xl font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
              Calendar
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as "google" | "outlook")}
              className="px-3 py-1.5 rounded-lg text-sm"
              style={{
                backgroundColor: darkMode ? "rgba(255,255,255,0.05)" : "#f6f8fa",
                color: darkMode ? "#e6edf3" : "#1e293b",
                border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
              }}
            >
              <option value="google">Google Calendar</option>
              <option value="outlook">Outlook</option>
            </select>

            <button
              onClick={() => setShowSettingsModal(true)}
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
          {!token ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div
                className="p-8 rounded-2xl text-center max-w-md"
                style={{
                  backgroundColor: darkMode ? "#161b22" : "#ffffff",
                  border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                }}
              >
                <Calendar className="w-16 h-16 mx-auto mb-4" style={{ color: "#6366f1" }} />
                <h2 className="text-xl font-semibold mb-2" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                  Connect Your Calendar
                </h2>
                <p className="text-sm mb-6" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Connect Google Calendar or Outlook to view and manage your events
                </p>
                <div className="flex flex-col gap-3">
                  <button
                    onClick={connectGoogle}
                    className="px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                    style={{ backgroundColor: "#6366f1", color: "#ffffff" }}
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#ffffff" d="M12 5c-3.87 0-7 3.13-7 7s3.13 7 7 7 7-3.13 7-7-3.13-7-7-7zm0 12c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z" />
                    </svg>
                    Connect Google Calendar
                  </button>
                  <button
                    onClick={connectOutlook}
                    className="px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                    style={{ backgroundColor: "#0078d4", color: "#ffffff" }}
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#ffffff" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                    </svg>
                    Connect Outlook
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))}
                    className="p-2 rounded-lg transition-colors hover:bg-white/5"
                    style={{ color: darkMode ? "#8b949e" : "#57606a" }}
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <h2 className="text-xl font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                    {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
                  </h2>
                  <button
                    onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))}
                    className="p-2 rounded-lg transition-colors hover:bg-white/5"
                    style={{ color: darkMode ? "#8b949e" : "#57606a" }}
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={fetchEvents}
                    className="p-2 rounded-lg transition-colors hover:bg-white/5"
                    style={{ color: darkMode ? "#8b949e" : "#57606a" }}
                    disabled={loading}
                  >
                    <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                  </button>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                    style={{ backgroundColor: "#6366f1", color: "#ffffff" }}
                  >
                    <Plus className="w-4 h-4" />
                    New Event
                  </button>
                </div>
              </div>

              <div
                className="rounded-xl overflow-hidden"
                style={{
                  backgroundColor: darkMode ? "#161b22" : "#ffffff",
                  border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                }}
              >
                <div className="grid grid-cols-7">
                  {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                    <div
                      key={day}
                      className="px-2 py-3 text-center text-sm font-medium"
                      style={{
                        backgroundColor: darkMode ? "#1c2128" : "#f6f8fa",
                        color: darkMode ? "#8b949e" : "#57606a",
                      }}
                    >
                      {day}
                    </div>
                  ))}
                  {days.map((day, idx) => {
                    const dayEvents = getEventsForDay(day);
                    const currentMonth = day.getMonth() === currentDate.getMonth();
                    return (
                      <div
                        key={idx}
                        className="min-h-24 p-2 border-b border-r cursor-pointer transition-colors hover:bg-white/5"
                        style={{
                          borderColor: darkMode ? "#30363d" : "#d0d7de",
                          opacity: currentMonth ? 1 : 0.4,
                        }}
                        onClick={() => {
                          if (dayEvents.length > 0 && dayEvents[0]) setSelectedEvent(dayEvents[0]);
                        }}
                      >
                        <div
                          className={`w-7 h-7 rounded-full flex items-center justify-center text-sm mb-1 ${
                            isToday(day) ? "text-white font-semibold" : ""
                          }`}
                          style={
                            isToday(day)
                              ? { backgroundColor: "#6366f1" }
                              : { color: darkMode ? "#e6edf3" : "#1e293b" }
                          }
                        >
                          {day.getDate()}
                        </div>
                        <div className="space-y-1">
                          {dayEvents.slice(0, 2).map((event) => (
                            <div
                              key={event.id}
                              className="text-xs px-1.5 py-0.5 rounded truncate"
                              style={{
                                backgroundColor: "rgba(99,102,241,0.2)",
                                color: "#6366f1",
                              }}
                            >
                              {event.summary}
                            </div>
                          ))}
                          {dayEvents.length > 2 && (
                            <div
                              className="text-xs px-1.5 py-0.5"
                              style={{ color: darkMode ? "#8b949e" : "#57606a" }}
                            >
                              +{dayEvents.length - 2} more
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {selectedEvent && (
        <div
          className="w-96 border-l p-6 overflow-auto"
          style={{
            backgroundColor: darkMode ? "#161b22" : "#ffffff",
            borderColor: darkMode ? "#30363d" : "#d0d7de",
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
              Event Details
            </h3>
            <button
              onClick={() => setSelectedEvent(null)}
              className="p-1 rounded hover:bg-white/5"
              style={{ color: darkMode ? "#8b949e" : "#57606a" }}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <h4 className="text-xl font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                {selectedEvent.summary}
              </h4>
            </div>

            <div className="flex items-center gap-2" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
              <Clock className="w-4 h-4" />
              <span className="text-sm">
                {new Date(selectedEvent.start_time).toLocaleString()} -{" "}
                {new Date(selectedEvent.end_time).toLocaleTimeString()}
              </span>
            </div>

            {selectedEvent.location && (
              <div className="flex items-center gap-2" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                <MapPin className="w-4 h-4" />
                <span className="text-sm">{selectedEvent.location}</span>
              </div>
            )}

            {selectedEvent.attendees && selectedEvent.attendees.length > 0 && (
              <div className="flex items-start gap-2" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                <Users className="w-4 h-4 mt-0.5" />
                <div className="text-sm">
                  {selectedEvent.attendees.map((email) => (
                    <div key={email}>{email}</div>
                  ))}
                </div>
              </div>
            )}

            {selectedEvent.description && (
              <div>
                <p className="text-sm" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  {selectedEvent.description}
                </p>
              </div>
            )}

            <div className="pt-4 border-t flex gap-2" style={{ borderColor: darkMode ? "#30363d" : "#d0d7de" }}>
              {selectedEvent.html_link && (
                <a
                  href={selectedEvent.html_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 px-3 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                  style={{
                    backgroundColor: "rgba(99,102,241,0.1)",
                    color: "#6366f1",
                  }}
                >
                  <ExternalLink className="w-4 h-4" />
                  Open
                </a>
              )}
              <button
                onClick={() => handleDeleteEvent(selectedEvent.id)}
                className="flex-1 px-3 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                style={{
                  backgroundColor: "rgba(248,81,73,0.1)",
                  color: "#f85149",
                }}
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div
            className="w-full max-w-lg rounded-xl p-6"
            style={{
              backgroundColor: darkMode ? "#161b22" : "#ffffff",
              border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
            }}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                Create Event
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded hover:bg-white/5"
                style={{ color: darkMode ? "#8b949e" : "#57606a" }}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Title
                </label>
                <input
                  type="text"
                  value={newEvent.summary}
                  onChange={(e) => setNewEvent({ ...newEvent, summary: e.target.value })}
                  placeholder="Event title"
                  className="w-full px-3 py-2 rounded-lg text-sm"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={newEvent.start_date}
                    onChange={(e) => setNewEvent({ ...newEvent, start_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg text-sm"
                    style={{
                      backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                      color: darkMode ? "#e6edf3" : "#1e293b",
                      border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                    }}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                    Start Time
                  </label>
                  <input
                    type="time"
                    value={newEvent.start_time}
                    onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg text-sm"
                    style={{
                      backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                      color: darkMode ? "#e6edf3" : "#1e293b",
                      border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                    End Date
                  </label>
                  <input
                    type="date"
                    value={newEvent.end_date}
                    onChange={(e) => setNewEvent({ ...newEvent, end_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg text-sm"
                    style={{
                      backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                      color: darkMode ? "#e6edf3" : "#1e293b",
                      border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                    }}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                    End Time
                  </label>
                  <input
                    type="time"
                    value={newEvent.end_time}
                    onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg text-sm"
                    style={{
                      backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                      color: darkMode ? "#e6edf3" : "#1e293b",
                      border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                    }}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Location
                </label>
                <input
                  type="text"
                  value={newEvent.location}
                  onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                  placeholder="Location or video call link"
                  className="w-full px-3 py-2 rounded-lg text-sm"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Attendees (comma-separated emails)
                </label>
                <input
                  type="text"
                  value={newEvent.attendees}
                  onChange={(e) => setNewEvent({ ...newEvent, attendees: e.target.value })}
                  placeholder="email@example.com, email2@example.com"
                  className="w-full px-3 py-2 rounded-lg text-sm"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Description
                </label>
                <textarea
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  placeholder="Event description"
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg text-sm resize-none"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 rounded-lg text-sm font-medium"
                  style={{
                    backgroundColor: darkMode ? "#21262d" : "#eaeef2",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateEvent}
                  className="flex-1 px-4 py-2 rounded-lg text-sm font-medium"
                  style={{ backgroundColor: "#6366f1", color: "#ffffff" }}
                >
                  Create Event
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showSettingsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div
            className="w-full max-w-md rounded-xl p-6"
            style={{
              backgroundColor: darkMode ? "#161b22" : "#ffffff",
              border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
            }}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                Calendar Settings
              </h3>
              <button
                onClick={() => setShowSettingsModal(false)}
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
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#4285f4" d="M12 5c-3.87 0-7 3.13-7 7s3.13 7 7 7 7-3.13 7-7-3.13-7-7-7zm0 12c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z" />
                    </svg>
                    <span className="font-medium" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                      Google Calendar
                    </span>
                  </div>
                  <span
                    className="text-xs px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: calendarConfig?.google?.configured
                        ? "rgba(63,185,80,0.2)"
                        : "rgba(248,81,73,0.2)",
                      color: calendarConfig?.google?.configured ? "#3fb950" : "#f85149",
                    }}
                  >
                    {calendarConfig?.google?.configured ? "Configured" : "Not configured"}
                  </span>
                </div>
                {!token && (
                  <button
                    onClick={connectGoogle}
                    className="w-full mt-2 px-3 py-1.5 rounded text-sm font-medium"
                    style={{ backgroundColor: "#4285f4", color: "#ffffff" }}
                  >
                    Connect Google
                  </button>
                )}
              </div>

              <div
                className="p-4 rounded-lg"
                style={{
                  backgroundColor: darkMode ? "#21262d" : "#f6f8fa",
                  border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#0078d4" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                    </svg>
                    <span className="font-medium" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                      Microsoft Outlook
                    </span>
                  </div>
                  <span
                    className="text-xs px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: calendarConfig?.outlook?.configured
                        ? "rgba(63,185,80,0.2)"
                        : "rgba(248,81,73,0.2)",
                      color: calendarConfig?.outlook?.configured ? "#3fb950" : "#f85149",
                    }}
                  >
                    {calendarConfig?.outlook?.configured ? "Configured" : "Not configured"}
                  </span>
                </div>
                {provider === "outlook" && !token && (
                  <button
                    onClick={connectOutlook}
                    className="w-full mt-2 px-3 py-1.5 rounded text-sm font-medium"
                    style={{ backgroundColor: "#0078d4", color: "#ffffff" }}
                  >
                    Connect Outlook
                  </button>
                )}
              </div>

              {token && (
                <div>
                  <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                    Access Token
                  </label>
                  <input
                    type="password"
                    value={token}
                    onChange={(e) => {
                      setToken(e.target.value);
                      localStorage.setItem("calendar_token", e.target.value);
                    }}
                    placeholder="Paste your OAuth access token"
                    className="w-full px-3 py-2 rounded-lg text-sm"
                    style={{
                      backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                      color: darkMode ? "#e6edf3" : "#1e293b",
                      border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                    }}
                  />
                  <button
                    onClick={() => {
                      setToken(null);
                      localStorage.removeItem("calendar_token");
                    }}
                    className="mt-2 text-sm"
                    style={{ color: "#f85149" }}
                  >
                    Disconnect Calendar
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
