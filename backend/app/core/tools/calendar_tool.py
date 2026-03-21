"""
Calendar Tool - Manage Google Calendar and Outlook Calendar events.
Gives agents the ability to schedule meetings, check availability, and manage calendars.
"""

import time
from datetime import datetime, timedelta
from typing import Literal

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel
from app.integrations.calendar import (
    GoogleCalendarService,
    OutlookCalendarService,
    CalendarConfig,
)


class CalendarTool(BaseTool):
    """
    Manage calendars via Google Calendar API and Microsoft Outlook.
    Configure via environment variables or tool config:
      GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET (Google)
      MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET (Outlook)
      Or use OAuth flow via the /api/calendar/authorize endpoint.

    Operations:
    - list_events: List upcoming calendar events
    - create_event: Create a new calendar event
    - update_event: Update an existing event
    - delete_event: Delete an event
    - search_events: Search for events by query
    - get_availability: Check free/busy times
    - list_calendars: List user's calendars
    """

    name = "calendar"
    description = (
        "Manage calendar events. "
        "Use 'list_events' to see upcoming events. "
        "Use 'create_event' to schedule meetings with attendees. "
        "Use 'search_events' to find specific events. "
        "Use 'get_availability' to check free/busy times. "
        "Supports Google Calendar and Microsoft Outlook."
    )
    category = ToolCategory.MISC
    risk_level = ToolRiskLevel.NORMAL

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'list_events', 'create_event', 'update_event', 'delete_event', 'search_events', 'get_availability', 'list_calendars'",
                required=True,
                enum=[
                    "list_events",
                    "create_event",
                    "update_event",
                    "delete_event",
                    "search_events",
                    "get_availability",
                    "list_calendars",
                ],
            ),
            "provider": ToolParameter(
                name="provider",
                type="string",
                description="Calendar provider: 'google' or 'outlook' (default: google)",
                required=False,
                default="google",
                enum=["google", "outlook"],
            ),
            "calendar_id": ToolParameter(
                name="calendar_id",
                type="string",
                description="Calendar ID to use (default: primary)",
                required=False,
                default="primary",
            ),
            "time_min": ToolParameter(
                name="time_min",
                type="string",
                description="Start time (ISO format or relative: 'today', 'tomorrow', 'in 1 hour')",
                required=False,
                default="now",
            ),
            "time_max": ToolParameter(
                name="time_max",
                type="string",
                description="End time (ISO format or relative: 'today', 'tomorrow', 'in 7 days')",
                required=False,
                default="in 7 days",
            ),
            "max_results": ToolParameter(
                name="max_results",
                type="integer",
                description="Maximum events to return (default 25, max 100)",
                required=False,
                default=25,
            ),
            "event_id": ToolParameter(
                name="event_id",
                type="string",
                description="Event ID (for update/delete operations)",
                required=False,
                default=None,
            ),
            "summary": ToolParameter(
                name="summary",
                type="string",
                description="Event title/summary (for create/update)",
                required=False,
                default=None,
            ),
            "description": ToolParameter(
                name="description",
                type="string",
                description="Event description",
                required=False,
                default=None,
            ),
            "location": ToolParameter(
                name="location",
                type="string",
                description="Event location (physical or video call link)",
                required=False,
                default=None,
            ),
            "start_time": ToolParameter(
                name="start_time",
                type="string",
                description="Event start time (ISO format or relative)",
                required=False,
                default=None,
            ),
            "end_time": ToolParameter(
                name="end_time",
                type="string",
                description="Event end time (ISO format or relative)",
                required=False,
                default=None,
            ),
            "attendees": ToolParameter(
                name="attendees",
                type="string",
                description="Comma-separated list of attendee emails",
                required=False,
                default=None,
            ),
            "timezone": ToolParameter(
                name="timezone",
                type="string",
                description="Timezone for the event (e.g. 'America/New_York', 'UTC')",
                required=False,
                default="UTC",
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query (for search_events)",
                required=False,
                default=None,
            ),
            "emails": ToolParameter(
                name="emails",
                type="string",
                description="Comma-separated emails for availability check",
                required=False,
                default=None,
            ),
        }

    def _validate_config(self) -> None:
        import os

        self.default_provider = self.config.get("default_provider", "google")
        self.default_timezone = self.config.get("timezone", "UTC")

    def _get_service(
        self, provider: str
    ) -> GoogleCalendarService | OutlookCalendarService | None:
        """Get the calendar service based on provider"""
        token = self.config.get(f"{provider}_token")
        if not token:
            token = os.getenv(f"{provider.upper()}_ACCESS_TOKEN")

        creds = {
            "client_id": self.config.get(f"{provider}_client_id")
            or os.getenv(f"{provider.upper()}_CLIENT_ID"),
            "client_secret": self.config.get(f"{provider}_client_secret")
            or os.getenv(f"{provider.upper()}_CLIENT_SECRET"),
        }

        config = CalendarConfig(
            provider=provider,
            credentials=creds,
            token=token,
            timezone=self.default_timezone,
        )

        if provider == "google":
            service = GoogleCalendarService(config)
        else:
            service = OutlookCalendarService(config)

        return service

    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime"""
        import os

        now = datetime.now()

        time_str_lower = time_str.lower().strip()

        if time_str_lower == "now":
            return now
        elif time_str_lower == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_str_lower == "tomorrow":
            return (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif time_str_lower.startswith("in "):
            parts = time_str_lower.split()
            if len(parts) >= 3:
                value = int(parts[1])
                unit = parts[2].rstrip("s")
                if unit == "minute":
                    return now + timedelta(minutes=value)
                elif unit == "hour":
                    return now + timedelta(hours=value)
                elif unit == "day":
                    return now + timedelta(days=value)
                elif unit == "week":
                    return now + timedelta(weeks=value)
        elif "+" in time_str or "-" in time_str[:10]:
            try:
                return datetime.fromisoformat(time_str)
            except ValueError:
                pass

        try:
            return datetime.fromisoformat(time_str)
        except ValueError:
            return now + timedelta(days=7)

    async def _list_events(
        self,
        service,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str,
        max_results: int,
    ) -> ToolResult:
        """List calendar events"""
        events = await service.get_events(time_min, time_max, calendar_id, max_results)

        if not events:
            return ToolResult(
                success=True,
                data={"events": [], "count": 0},
                stdout="No events found in the specified time range.",
            )

        lines = [f"Calendar Events ({len(events)}):\n"]
        for i, event in enumerate(events, 1):
            start = (
                event.start_time.strftime("%Y-%m-%d %H:%M")
                if event.start_time
                else "TBD"
            )
            end = event.end_time.strftime("%H:%M") if event.end_time else ""
            lines.append(f"{i}. {event.summary}")
            lines.append(f"   {start} - {end}")
            if event.location:
                lines.append(f"   Location: {event.location}")
            if event.attendees:
                lines.append(f"   Attendees: {len(event.attendees)}")
            lines.append("")

        return ToolResult(
            success=True,
            data={"events": [e.to_dict() for e in events], "count": len(events)},
            stdout="\n".join(lines),
        )

    async def _create_event(
        self,
        service,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str | None,
        location: str | None,
        attendees: list[str],
        timezone: str,
        calendar_id: str,
    ) -> ToolResult:
        """Create a calendar event"""
        if not summary:
            return ToolResult(
                success=False, error="summary is required for create_event"
            )

        if not start_time or not end_time:
            return ToolResult(
                success=False, error="start_time and end_time are required"
            )

        if end_time <= start_time:
            return ToolResult(success=False, error="end_time must be after start_time")

        event = await service.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees if attendees else None,
            timezone=timezone,
            calendar_id=calendar_id if calendar_id != "primary" else None,
        )

        if not event.id:
            return ToolResult(success=False, error="Failed to create event")

        lines = [
            f"Event Created: {event.summary}",
            f"ID: {event.id}",
            f"Start: {event.start_time}",
            f"End: {event.end_time}",
        ]
        if event.location:
            lines.append(f"Location: {event.location}")
        if event.html_link:
            lines.append(f"Link: {event.html_link}")
        if event.attendees:
            lines.append(f"Attendees: {', '.join(event.attendees)}")

        return ToolResult(
            success=True,
            data=event.to_dict(),
            stdout="\n".join(lines),
        )

    async def _update_event(
        self,
        service,
        event_id: str,
        summary: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        description: str | None,
        location: str | None,
        attendees: list[str] | None,
        calendar_id: str,
    ) -> ToolResult:
        """Update a calendar event"""
        if not event_id:
            return ToolResult(
                success=False, error="event_id is required for update_event"
            )

        event = await service.update_event(
            event_id=event_id,
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees,
            calendar_id=calendar_id if calendar_id != "primary" else None,
        )

        if not event.id:
            return ToolResult(success=False, error="Failed to update event")

        return ToolResult(
            success=True,
            data=event.to_dict(),
            stdout=f"Event Updated: {event.summary}",
        )

    async def _delete_event(
        self, service, event_id: str, calendar_id: str
    ) -> ToolResult:
        """Delete a calendar event"""
        if not event_id:
            return ToolResult(
                success=False, error="event_id is required for delete_event"
            )

        success = await service.delete_event(
            event_id=event_id,
            calendar_id=calendar_id if calendar_id != "primary" else None,
        )

        if success:
            return ToolResult(success=True, stdout=f"Event {event_id} deleted")
        return ToolResult(success=False, error=f"Failed to delete event {event_id}")

    async def _search_events(
        self, service, query: str, calendar_id: str, max_results: int
    ) -> ToolResult:
        """Search calendar events"""
        if not query:
            return ToolResult(
                success=False, error="query is required for search_events"
            )

        events = await service.search_events(
            query, calendar_id if calendar_id != "primary" else None, max_results
        )

        if not events:
            return ToolResult(
                success=True,
                data={"events": [], "count": 0},
                stdout=f"No events found matching '{query}'",
            )

        lines = [f"Search Results for '{query}' ({len(events)}):\n"]
        for i, event in enumerate(events, 1):
            start = (
                event.start_time.strftime("%Y-%m-%d %H:%M")
                if event.start_time
                else "TBD"
            )
            lines.append(f"{i}. {event.summary} ({start})")

        return ToolResult(
            success=True,
            data={"events": [e.to_dict() for e in events], "count": len(events)},
            stdout="\n".join(lines),
        )

    async def _get_availability(
        self,
        service,
        emails: list[str],
        time_min: datetime,
        time_max: datetime,
    ) -> ToolResult:
        """Get free/busy availability"""
        if not emails:
            return ToolResult(
                success=False, error="emails is required for get_availability"
            )

        results = await service.get_free_busy(emails, time_min, time_max)

        lines = ["Free/Busy Availability:\n"]
        for result in results:
            status = "BUSY" if result.busy else "FREE"
            lines.append(f"{result.email}: {status}")
            if result.events:
                for evt in result.events[:3]:
                    start = evt.start_time.strftime("%H:%M") if evt.start_time else ""
                    end = evt.end_time.strftime("%H:%M") if evt.end_time else ""
                    lines.append(f"  - {start} to {end}")

        return ToolResult(
            success=True,
            data={
                "results": [
                    {"email": r.email, "busy": r.busy, "events": len(r.events)}
                    for r in results
                ]
            },
            stdout="\n".join(lines),
        )

    async def _list_calendars(self, service) -> ToolResult:
        """List user's calendars"""
        calendars = await service.get_calendar_list()

        if not calendars:
            return ToolResult(
                success=True,
                data={"calendars": [], "count": 0},
                stdout="No calendars found",
            )

        lines = [f"Calendars ({len(calendars)}):\n"]
        for cal in calendars:
            primary = " (Primary)" if cal.primary else ""
            lines.append(f"- {cal.summary}{primary} [{cal.id}]")

        return ToolResult(
            success=True,
            data={
                "calendars": [
                    {"id": c.id, "summary": c.summary, "primary": c.primary}
                    for c in calendars
                ]
            },
            stdout="\n".join(lines),
        )

    async def execute(
        self,
        operation: str,
        provider: str = "google",
        calendar_id: str = "primary",
        time_min: str = "now",
        time_max: str = "in 7 days",
        max_results: int = 25,
        event_id: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        location: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        attendees: str | None = None,
        timezone: str = "UTC",
        query: str | None = None,
        emails: str | None = None,
    ) -> ToolResult:
        start_time_exec = time.time()

        try:
            service = self._get_service(provider)
            if not service:
                return ToolResult(
                    success=False,
                    error=f"Calendar provider '{provider}' not configured. Set {provider.upper()}_CLIENT_ID and {provider.upper()}_CLIENT_SECRET, or use OAuth flow.",
                )

            initialized = await service.initialize()
            if not initialized:
                return ToolResult(
                    success=False,
                    error=f"Failed to initialize {provider} calendar service",
                )

            authenticated = await service.is_authenticated()
            if not authenticated:
                return ToolResult(
                    success=False,
                    error=f"Not authenticated with {provider}. Complete OAuth flow via /api/calendar/authorize",
                )

            time_min_dt = self._parse_time(time_min)
            time_max_dt = self._parse_time(time_max)

            start_dt = self._parse_time(start_time) if start_time else None
            end_dt = self._parse_time(end_time) if end_time else None

            attendee_list = (
                [a.strip() for a in attendees.split(",")] if attendees else []
            )

            match operation:
                case "list_events":
                    result = await self._list_events(
                        service, time_min_dt, time_max_dt, calendar_id, max_results
                    )
                case "create_event":
                    result = await self._create_event(
                        service,
                        summary or "",
                        start_dt,
                        end_dt,
                        description,
                        location,
                        attendee_list,
                        timezone,
                        calendar_id,
                    )
                case "update_event":
                    result = await self._update_event(
                        service,
                        event_id or "",
                        summary,
                        start_dt,
                        end_dt,
                        description,
                        location,
                        attendee_list if attendee_list else None,
                        calendar_id,
                    )
                case "delete_event":
                    result = await self._delete_event(
                        service, event_id or "", calendar_id
                    )
                case "search_events":
                    result = await self._search_events(
                        service, query or "", calendar_id, max_results
                    )
                case "get_availability":
                    result = await self._get_availability(
                        service, attendee_list, time_min_dt, time_max_dt
                    )
                case "list_calendars":
                    result = await self._list_calendars(service)
                case _:
                    result = ToolResult(
                        success=False, error=f"Unknown operation: {operation}"
                    )

            result.execution_time_ms = int((time.time() - start_time_exec) * 1000)
            return result

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Calendar operation failed: {e}",
                execution_time_ms=int((time.time() - start_time_exec) * 1000),
            )
