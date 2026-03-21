"""
Calendar Integration Package
Supports Google Calendar and Microsoft Outlook Calendar
"""

from .google_calendar import GoogleCalendarService
from .outlook_calendar import OutlookCalendarService
from .base_calendar import BaseCalendarService, CalendarEvent, CalendarConfig

__all__ = [
    "GoogleCalendarService",
    "OutlookCalendarService",
    "BaseCalendarService",
    "CalendarEvent",
    "CalendarConfig",
]
