"""
Google Calendar Service Implementation
Integrates with Google Calendar API v3
"""

import os
from datetime import datetime
from typing import Any

from .base_calendar import (
    BaseCalendarService,
    CalendarConfig,
    CalendarEvent,
    CalendarListEntry,
    FreeBusyResult,
)


class GoogleCalendarService(BaseCalendarService):
    """
    Google Calendar API v3 integration.

    Requires:
    - GOOGLE_CLIENT_ID
    - GOOGLE_CLIENT_SECRET
    - OAuth tokens stored securely

    Scopes needed:
    - https://www.googleapis.com/auth/calendar
    - https://www.googleapis.com/auth/calendar.events
    """

    BASE_URL = "https://www.googleapis.com/calendar/v3"

    def __init__(self, config: CalendarConfig | None = None):
        super().__init__(config)
        self.client_id: str | None = None
        self.client_secret: str | None = None
        self._http_client: Any = None

    async def initialize(self) -> bool:
        """Initialize with Google OAuth credentials"""
        self.client_id = self.config.credentials.get("client_id") or os.getenv(
            "GOOGLE_CLIENT_ID"
        )
        self.client_secret = self.config.credentials.get("client_secret") or os.getenv(
            "GOOGLE_CLIENT_SECRET"
        )

        if not self.client_id or not self.client_secret:
            return False

        self._initialized = True
        return True

    async def is_authenticated(self) -> bool:
        """Check if we have a valid access token"""
        return bool(self.config.token) and self._initialized

    def _get_headers(self) -> dict[str, str]:
        """Build authorization headers"""
        return {
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> dict | None:
        """Make authenticated request to Google Calendar API"""
        import httpx

        if not self.config.token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/{endpoint}"
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    json=data,
                    params=params,
                    timeout=30,
                )

                if response.status_code in (200, 201):
                    return response.json() if response.text else {}
                return None
        except Exception:
            return None

    def _parse_event(self, raw: dict) -> CalendarEvent:
        """Parse Google Calendar event to our format"""
        start = raw.get("start", {})
        end = raw.get("end", {})

        start_dt = None
        end_dt = None

        if start.get("dateTime"):
            start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
        elif start.get("date"):
            start_dt = datetime.fromisoformat(start["date"])

        if end.get("dateTime"):
            end_dt = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
        elif end.get("date"):
            end_dt = datetime.fromisoformat(end["date"])

        attendees = []
        for a in raw.get("attendees", []):
            if isinstance(a, dict):
                attendees.append(a.get("email", ""))
            elif isinstance(a, str):
                attendees.append(a)

        organizer = raw.get("organizer", {})
        if isinstance(organizer, dict):
            organizer = organizer.get("email")

        return CalendarEvent(
            id=raw.get("id"),
            summary=raw.get("summary", ""),
            description=raw.get("description", ""),
            location=raw.get("location"),
            start_time=start_dt,
            end_time=end_dt,
            timezone=start.get("timeZone", "UTC"),
            attendees=[a for a in attendees if a],
            organizer=organizer,
            color_id=int(raw.get("colorId", 0)) if raw.get("colorId") else None,
            status=raw.get("status", "confirmed"),
            html_link=raw.get("htmlLink"),
            recurrence=raw.get("recurrence", []),
            reminders=raw.get("reminders", {"useDefault": True}),
        )

    def _build_event_payload(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str | None,
        location: str | None,
        attendees: list[str] | None,
        timezone: str,
    ) -> dict:
        """Build Google Calendar API event payload"""
        payload: dict[str, Any] = {
            "summary": summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": timezone,
            },
        }

        if description:
            payload["description"] = description
        if location:
            payload["location"] = location
        if attendees:
            payload["attendees"] = [{"email": a} for a in attendees]

        return payload

    async def get_events(
        self,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        calendar_id: str | None = None,
        max_results: int = 100,
    ) -> list[CalendarEvent]:
        """Get calendar events"""
        cal_id = calendar_id or self.config.calendar_id
        params: dict[str, Any] = {
            "maxResults": min(max_results, 250),
            "singleEvents": True,
            "orderBy": "startTime",
        }

        if time_min:
            params["timeMin"] = time_min.isoformat()
        if time_max:
            params["timeMax"] = time_max.isoformat()

        result = await self._make_request(
            "GET",
            f"calendars/{cal_id}/events",
            params=params,
        )

        if not result:
            return []

        events = []
        for item in result.get("items", []):
            events.append(self._parse_event(item))

        return events

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
        cal_id = calendar_id or self.config.calendar_id
        tz = timezone or self.config.timezone

        payload = self._build_event_payload(
            summary,
            start_time,
            end_time,
            description,
            location,
            attendees,
            tz,
        )

        result = await self._make_request(
            "POST",
            f"calendars/{cal_id}/events",
            data=payload,
        )

        if not result:
            return CalendarEvent()

        return self._parse_event(result)

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
        cal_id = calendar_id or self.config.calendar_id

        payload: dict[str, Any] = {}
        if summary:
            payload["summary"] = summary
        if description:
            payload["description"] = description
        if location:
            payload["location"] = location
        if start_time and end_time:
            tz = self.config.timezone
            payload["start"] = {"dateTime": start_time.isoformat(), "timeZone": tz}
            payload["end"] = {"dateTime": end_time.isoformat(), "timeZone": tz}
        if attendees:
            payload["attendees"] = [{"email": a} for a in attendees]

        result = await self._make_request(
            "PATCH",
            f"calendars/{cal_id}/events/{event_id}",
            data=payload,
        )

        if not result:
            return CalendarEvent()

        return self._parse_event(result)

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str | None = None,
    ) -> bool:
        """Delete a calendar event"""
        cal_id = calendar_id or self.config.calendar_id

        result = await self._make_request(
            "DELETE",
            f"calendars/{cal_id}/events/{event_id}",
        )

        return result is not None

    async def get_calendar_list(self) -> list[CalendarListEntry]:
        """Get list of user's calendars"""
        result = await self._make_request("GET", "users/me/calendarList")

        if not result:
            return []

        calendars = []
        for item in result.get("items", []):
            calendars.append(
                CalendarListEntry(
                    id=item.get("id", ""),
                    summary=item.get("summary", ""),
                    primary=item.get("primary", False),
                    access_role=item.get("accessRole", "freeBusyReader"),
                    background_color=item.get("backgroundColor"),
                    foreground_color=item.get("foregroundColor"),
                )
            )

        return calendars

    async def get_free_busy(
        self,
        emails: list[str],
        time_min: datetime,
        time_max: datetime,
    ) -> list[FreeBusyResult]:
        """Get free/busy information"""
        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": email} for email in emails],
        }

        result = await self._make_request(
            "POST",
            "freeBusy",
            data=body,
        )

        if not result:
            return []

        results = []
        calendars = result.get("calendars", {})

        for email in emails:
            cal_data = calendars.get(email, {})
            busy_slots = cal_data.get("busy", [])

            events = []
            for slot in busy_slots:
                start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
                events.append(
                    CalendarEvent(
                        start_time=start,
                        end_time=end,
                        status="confirmed",
                    )
                )

            results.append(
                FreeBusyResult(
                    email=email,
                    start=time_min,
                    end=time_max,
                    busy=bool(busy_slots),
                    events=events,
                )
            )

        return results

    async def search_events(
        self,
        query: str,
        calendar_id: str | None = None,
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        """Search calendar events"""
        cal_id = calendar_id or self.config.calendar_id

        result = await self._make_request(
            "GET",
            f"calendars/{cal_id}/events",
            params={
                "q": query,
                "maxResults": min(max_results, 100),
                "singleEvents": True,
            },
        )

        if not result:
            return []

        events = []
        for item in result.get("items", []):
            events.append(self._parse_event(item))

        return events
