"""
Base Calendar Service - Abstract interface for calendar integrations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class CalendarEvent:
    """Represents a calendar event"""

    id: str | None = None
    summary: str = ""
    description: str = ""
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str = "UTC"
    attendees: list[str] = field(default_factory=list)
    organizer: str | None = None
    color_id: int | None = None
    status: Literal["confirmed", "tentative", "cancelled"] = "confirmed"
    html_link: str | None = None
    recurrence: list[str] = field(default_factory=list)
    reminders: dict = field(default_factory=lambda: {"use_default": True})

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "summary": self.summary,
            "description": self.description,
            "location": self.location,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "timezone": self.timezone,
            "attendees": self.attendees,
            "organizer": self.organizer,
            "color_id": self.color_id,
            "status": self.status,
            "html_link": self.html_link,
        }


@dataclass
class CalendarConfig:
    """Configuration for calendar integration"""

    provider: Literal["google", "outlook"] = "google"
    credentials: dict = field(default_factory=dict)
    token: str | None = None
    refresh_token: str | None = None
    calendar_id: str = "primary"
    timezone: str = "UTC"


@dataclass
class CalendarListEntry:
    """Calendar list entry"""

    id: str
    summary: str
    primary: bool = False
    access_role: str = "freeBusyReader"
    background_color: str | None = None
    foreground_color: str | None = None


@dataclass
class FreeBusyResult:
    """Free/busy information for a time range"""

    email: str
    start: datetime
    end: datetime
    busy: bool
    events: list[CalendarEvent] = field(default_factory=list)


class BaseCalendarService(ABC):
    """Abstract base class for calendar integrations"""

    def __init__(self, config: CalendarConfig | None = None):
        self.config = config or CalendarConfig()
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the calendar service with OAuth credentials"""
        pass

    @abstractmethod
    async def is_authenticated(self) -> bool:
        """Check if the service has valid authentication"""
        pass

    @abstractmethod
    async def get_events(
        self,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        calendar_id: str | None = None,
        max_results: int = 100,
    ) -> list[CalendarEvent]:
        """Get calendar events within a time range"""
        pass

    @abstractmethod
    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        calendar_id: str | None = None,
        timezone: str | None = None,
    ) -> CalendarEvent:
        """Create a new calendar event"""
        pass

    @abstractmethod
    async def update_event(
        self,
        event_id: str,
        summary: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        calendar_id: str | None = None,
    ) -> CalendarEvent:
        """Update an existing calendar event"""
        pass

    @abstractmethod
    async def delete_event(
        self,
        event_id: str,
        calendar_id: str | None = None,
    ) -> bool:
        """Delete a calendar event"""
        pass

    @abstractmethod
    async def get_calendar_list(self) -> list[CalendarListEntry]:
        """Get list of user's calendars"""
        pass

    @abstractmethod
    async def get_free_busy(
        self,
        emails: list[str],
        time_min: datetime,
        time_max: datetime,
    ) -> list[FreeBusyResult]:
        """Get free/busy information for multiple users"""
        pass

    @abstractmethod
    async def search_events(
        self,
        query: str,
        calendar_id: str | None = None,
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        """Search for calendar events"""
        pass

    async def close(self) -> None:
        """Cleanup resources"""
        pass
