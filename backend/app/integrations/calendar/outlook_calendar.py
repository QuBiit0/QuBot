"""
Microsoft Outlook Calendar Service Implementation
Integrates with Microsoft Graph API
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


class OutlookCalendarService(BaseCalendarService):
    """
    Microsoft Outlook Calendar via Graph API.

    Requires:
    - MICROSOFT_CLIENT_ID
    - MICROSOFT_CLIENT_SECRET
    - OAuth tokens stored securely

    Permissions needed:
    - Calendar.Read
    - Calendar.ReadWrite
    - Calendars.Read
    - Calendars.ReadWrite
    """

    BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, config: CalendarConfig | None = None):
        super().__init__(config)
        self.client_id: str | None = None
        self.client_secret: str | None = None
        self.tenant_id: str | None = None
        self._http_client: Any = None

    async def initialize(self) -> bool:
        """Initialize with Microsoft OAuth credentials"""
        self.client_id = self.config.credentials.get("client_id") or os.getenv(
            "MICROSOFT_CLIENT_ID"
        )
        self.client_secret = self.config.credentials.get("client_secret") or os.getenv(
            "MICROSOFT_CLIENT_SECRET"
        )
        self.tenant_id = self.config.credentials.get("tenant_id") or os.getenv(
            "MICROSOFT_TENANT_ID", "common"
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
        """Make authenticated request to Microsoft Graph API"""
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
        """Parse Microsoft Graph event to our format"""
        start = raw.get("start", {})
        end = raw.get("end", {})

        start_dt = None
        end_dt = None

        if start.get("dateTime"):
            start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
        if end.get("dateTime"):
            end_dt = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))

        attendees = []
        for a in raw.get("attendees", []):
            if isinstance(a, dict):
                email = a.get("emailAddress", {}).get("address", "")
                if email:
                    attendees.append(email)

        organizer = raw.get("organizer", {})
        if isinstance(organizer, dict):
            organizer = organizer.get("emailAddress", {}).get("name")

        categories = raw.get("categories", [])

        return CalendarEvent(
            id=raw.get("id"),
            summary=raw.get("subject", ""),
            description=raw.get("bodyPreview", "")
            or raw.get("body", {}).get("content", ""),
            location=raw.get("location", {}).get("displayName"),
            start_time=start_dt,
            end_time=end_dt,
            timezone=start.get("timeZone", "UTC"),
            attendees=attendees,
            organizer=organizer,
            color_id=None,
            status=raw.get("showAs", "free"),
            html_link=raw.get("webLink"),
            recurrence=[],
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
        """Build Microsoft Graph event payload"""
        payload: dict[str, Any] = {
            "subject": summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": timezone,
            },
            "isAllDay": False,
        }

        if description:
            payload["body"] = {
                "contentType": "text",
                "content": description,
            }
        if location:
            payload["location"] = {"displayName": location}
        if attendees:
            payload["attendees"] = [
                {
                    "emailAddress": {"address": a},
                    "type": "required",
                }
                for a in attendees
            ]

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

        if cal_id == "primary":
            endpoint = "me/calendar/events"
        else:
            endpoint = f"me/calendars/{cal_id}/events"

        params: dict[str, Any] = {
            "$top": min(max_results, 1000),
            "$orderby": "start/dateTime",
            "$select": "id,subject,bodyPreview,body,start,end,location,attendees,organizer,showAs,categories,webLink",
        }

        if time_min:
            params["$filter"] = f"start/dateTime ge '{time_min.isoformat()}'"
        if time_max:
            if params.get("$filter"):
                params["$filter"] += f" and end/dateTime le '{time_max.isoformat()}'"
            else:
                params["$filter"] = f"end/dateTime le '{time_max.isoformat()}'"

        result = await self._make_request("GET", endpoint, params=params)

        if not result:
            return []

        events = []
        for item in result.get("value", []):
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

        if cal_id == "primary":
            endpoint = "me/calendar/events"
        else:
            endpoint = f"me/calendars/{cal_id}/events"

        payload = self._build_event_payload(
            summary,
            start_time,
            end_time,
            description,
            location,
            attendees,
            tz,
        )

        result = await self._make_request("POST", endpoint, data=payload)

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
        tz = self.config.timezone

        if cal_id == "primary":
            endpoint = f"me/calendar/events/{event_id}"
        else:
            endpoint = f"me/calendars/{cal_id}/events/{event_id}"

        payload: dict[str, Any] = {}
        if summary:
            payload["subject"] = summary
        if description:
            payload["body"] = {"contentType": "text", "content": description}
        if location:
            payload["location"] = {"displayName": location}
        if start_time and end_time:
            payload["start"] = {"dateTime": start_time.isoformat(), "timeZone": tz}
            payload["end"] = {"dateTime": end_time.isoformat(), "timeZone": tz}
        if attendees:
            payload["attendees"] = [
                {"emailAddress": {"address": a}, "type": "required"} for a in attendees
            ]

        result = await self._make_request("PATCH", endpoint, data=payload)

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

        if cal_id == "primary":
            endpoint = f"me/calendar/events/{event_id}"
        else:
            endpoint = f"me/calendars/{cal_id}/events/{event_id}"

        result = await self._make_request("DELETE", endpoint)
        return result is not None

    async def get_calendar_list(self) -> list[CalendarListEntry]:
        """Get list of user's calendars"""
        result = await self._make_request("GET", "me/calendars")

        if not result:
            return []

        calendars = []
        for item in result.get("value", []):
            calendars.append(
                CalendarListEntry(
                    id=item.get("id", ""),
                    summary=item.get("name", ""),
                    primary=item.get("isDefaultCalendar", False),
                    access_role=item.get("role", "freeBusyReader"),
                    background_color=item.get("hexColor"),
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
            "timeWindow": {
                "startTime": time_min.isoformat(),
                "endTime": time_max.isoformat(),
            },
            "availabilityViewInterval": 30,
            "schedules": emails,
        }

        result = await self._make_request("POST", "me/calendar/getSchedule", data=body)

        if not result:
            return []

        results = []
        schedule_items = result.get("value", [])

        for schedule in schedule_items:
            email = schedule.get("scheduleId", "")
            busy_slots = []

            for item in schedule.get("scheduleItems", []):
                if item.get("status") != "free":
                    start = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(item["end"].replace("Z", "+00:00"))
                    busy_slots.append(
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
                    busy=len(busy_slots) > 0,
                    events=busy_slots,
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

        if cal_id == "primary":
            endpoint = "me/calendar/events"
        else:
            endpoint = f"me/calendars/{cal_id}/events"

        params = {
            "$filter": f"contains(subject,'{query}')",
            "$top": min(max_results, 100),
        }

        result = await self._make_request("GET", endpoint, params=params)

        if not result:
            return []

        events = []
        for item in result.get("value", []):
            events.append(self._parse_event(item))

        return events
