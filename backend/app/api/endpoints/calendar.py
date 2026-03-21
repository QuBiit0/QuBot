"""
Calendar API Endpoints
OAuth flows and calendar management for Google Calendar and Microsoft Outlook
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ...core.security import get_current_user
from ...models.user import User

router = APIRouter(prefix="/calendar", tags=["calendar"])


# ============================================================================
# Pydantic Models
# ============================================================================


class CalendarEventCreate(BaseModel):
    provider: Literal["google", "outlook"] = "google"
    calendar_id: str = "primary"
    summary: str
    description: str | None = None
    location: str | None = None
    start_time: datetime
    end_time: datetime
    attendees: list[str] | None = None
    timezone: str = "UTC"


class CalendarEventUpdate(BaseModel):
    event_id: str
    provider: Literal["google", "outlook"] = "google"
    calendar_id: str = "primary"
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    attendees: list[str] | None = None


class CalendarQuery(BaseModel):
    provider: Literal["google", "outlook"] = "google"
    calendar_id: str = "primary"
    time_min: datetime | None = None
    time_max: datetime | None = None
    max_results: int = 25


# ============================================================================
# OAuth Configuration
# ============================================================================


def get_google_oauth_config() -> dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/calendar/google/callback"
    )
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
        ],
    }


def get_outlook_oauth_config() -> dict:
    client_id = os.getenv("MICROSOFT_CLIENT_ID", "")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
    redirect_uri = os.getenv(
        "MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/calendar/outlook/callback"
    )
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "tenant_id": tenant_id,
        "redirect_uri": redirect_uri,
        "auth_url": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
        "token_url": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        "scopes": [
            "offline_access",
            "Calendars.Read",
            "Calendars.ReadWrite",
        ],
    }


# ============================================================================
# OAuth Endpoints - Google Calendar
# ============================================================================


@router.get("/google/authorize")
async def google_authorize(request: Request):
    """Start Google OAuth flow"""
    config = get_google_oauth_config()

    if not config["client_id"]:
        raise HTTPException(
            status_code=400,
            detail="Google Calendar not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET",
        )

    import httpx
    from urllib.parse import urlencode

    state = str(datetime.now().timestamp())
    request.session["oauth_state"] = state
    request.session["oauth_provider"] = "google"

    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": " ".join(config["scopes"]),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    auth_url = f"{config['auth_url']}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(code: str = Query(...), state: str | None = Query(None)):
    """Handle Google OAuth callback"""
    config = get_google_oauth_config()

    if not config["client_id"] or not config["client_secret"]:
        raise HTTPException(status_code=400, detail="Google Calendar not configured")

    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            config["token_url"],
            data={
                "code": code,
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "redirect_uri": config["redirect_uri"],
                "grant_type": "authorization_code",
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to exchange code for token"
            )

        token_data = response.json()

    return {
        "success": True,
        "provider": "google",
        "message": "Google Calendar connected successfully",
        "token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
    }


# ============================================================================
# OAuth Endpoints - Microsoft Outlook
# ============================================================================


@router.get("/outlook/authorize")
async def outlook_authorize(request: Request):
    """Start Microsoft OAuth flow"""
    config = get_outlook_oauth_config()

    if not config["client_id"]:
        raise HTTPException(
            status_code=400,
            detail="Outlook Calendar not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET",
        )

    import httpx
    from urllib.parse import urlencode

    state = str(datetime.now().timestamp())

    params = {
        "client_id": config["client_id"],
        "response_type": "code",
        "redirect_uri": config["redirect_uri"],
        "scope": " ".join(config["scopes"]),
        "state": state,
        "response_mode": "query",
    }

    auth_url = f"{config['auth_url']}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/outlook/callback")
async def outlook_callback(code: str = Query(...), state: str | None = Query(None)):
    """Handle Microsoft OAuth callback"""
    config = get_outlook_oauth_config()

    if not config["client_id"] or not config["client_secret"]:
        raise HTTPException(status_code=400, detail="Outlook Calendar not configured")

    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            config["token_url"],
            data={
                "code": code,
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "redirect_uri": config["redirect_uri"],
                "grant_type": "authorization_code",
                "scope": " ".join(config["scopes"]),
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to exchange code for token"
            )

        token_data = response.json()

    return {
        "success": True,
        "provider": "outlook",
        "message": "Outlook Calendar connected successfully",
        "token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
    }


# ============================================================================
# Calendar Status
# ============================================================================


@router.get("/status")
async def calendar_status():
    """Check calendar integration status"""
    google_config = get_google_oauth_config()
    outlook_config = get_outlook_oauth_config()

    return {
        "google": {
            "configured": bool(
                google_config["client_id"] and google_config["client_secret"]
            ),
            "client_id_set": bool(google_config["client_id"]),
        },
        "outlook": {
            "configured": bool(
                outlook_config["client_id"] and outlook_config["client_secret"]
            ),
            "client_id_set": bool(outlook_config["client_id"]),
        },
    }


@router.get("/schemas")
async def calendar_schemas():
    """Get calendar configuration schemas"""
    from .integrations import CALENDAR_CONFIG_SCHEMAS

    return {"data": CALENDAR_CONFIG_SCHEMAS}


# ============================================================================
# Calendar CRUD Operations (require token)
# ============================================================================


@router.get("/events")
async def list_events(
    provider: Literal["google", "outlook"] = Query("google"),
    calendar_id: str = Query("primary"),
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    max_results: int = Query(25, ge=1, le=250),
    token: str | None = None,
):
    """List calendar events"""
    if not token:
        raise HTTPException(status_code=401, detail="Calendar token required")

    from ..integrations.calendar import (
        GoogleCalendarService,
        OutlookCalendarService,
        CalendarConfig,
    )

    config = CalendarConfig(provider=provider, token=token)

    if provider == "google":
        service = GoogleCalendarService(config)
    else:
        service = OutlookCalendarService(config)

    await service.initialize()

    if not time_min:
        time_min = datetime.now()
    if not time_max:
        time_max = time_min + timedelta(days=7)

    events = await service.get_events(time_min, time_max, calendar_id, max_results)

    return {
        "success": True,
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.post("/events")
async def create_event(event: CalendarEventCreate, token: str | None = None):
    """Create a calendar event"""
    if not token:
        raise HTTPException(status_code=401, detail="Calendar token required")

    from ..integrations.calendar import (
        GoogleCalendarService,
        OutlookCalendarService,
        CalendarConfig,
    )

    config = CalendarConfig(provider=event.provider, token=token)

    if event.provider == "google":
        service = GoogleCalendarService(config)
    else:
        service = OutlookCalendarService(config)

    await service.initialize()

    created = await service.create_event(
        summary=event.summary,
        start_time=event.start_time,
        end_time=event.end_time,
        description=event.description,
        location=event.location,
        attendees=event.attendees,
        calendar_id=event.calendar_id if event.calendar_id != "primary" else None,
        timezone=event.timezone,
    )

    return {
        "success": True,
        "event": created.to_dict(),
    }


@router.patch("/events")
async def update_event(event: CalendarEventUpdate, token: str | None = None):
    """Update a calendar event"""
    if not token:
        raise HTTPException(status_code=401, detail="Calendar token required")

    from ..integrations.calendar import (
        GoogleCalendarService,
        OutlookCalendarService,
        CalendarConfig,
    )

    config = CalendarConfig(provider=event.provider, token=token)

    if event.provider == "google":
        service = GoogleCalendarService(config)
    else:
        service = OutlookCalendarService(config)

    await service.initialize()

    updated = await service.update_event(
        event_id=event.event_id,
        summary=event.summary,
        start_time=event.start_time,
        end_time=event.end_time,
        description=event.description,
        location=event.location,
        attendees=event.attendees,
        calendar_id=event.calendar_id if event.calendar_id != "primary" else None,
    )

    return {
        "success": True,
        "event": updated.to_dict(),
    }


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    provider: Literal["google", "outlook"] = Query("google"),
    calendar_id: str = Query("primary"),
    token: str | None = None,
):
    """Delete a calendar event"""
    if not token:
        raise HTTPException(status_code=401, detail="Calendar token required")

    from ..integrations.calendar import (
        GoogleCalendarService,
        OutlookCalendarService,
        CalendarConfig,
    )

    config = CalendarConfig(provider=provider, token=token)

    if provider == "google":
        service = GoogleCalendarService(config)
    else:
        service = OutlookCalendarService(config)

    await service.initialize()

    success = await service.delete_event(
        event_id=event_id,
        calendar_id=calendar_id if calendar_id != "primary" else None,
    )

    return {
        "success": success,
        "message": f"Event {event_id} deleted" if success else "Failed to delete event",
    }


@router.get("/calendars")
async def list_calendars(
    provider: Literal["google", "outlook"] = Query("google"),
    token: str | None = None,
):
    """List user's calendars"""
    if not token:
        raise HTTPException(status_code=401, detail="Calendar token required")

    from ..integrations.calendar import (
        GoogleCalendarService,
        OutlookCalendarService,
        CalendarConfig,
    )

    config = CalendarConfig(provider=provider, token=token)

    if provider == "google":
        service = GoogleCalendarService(config)
    else:
        service = OutlookCalendarService(config)

    await service.initialize()

    calendars = await service.get_calendar_list()

    return {
        "success": True,
        "calendars": [
            {
                "id": c.id,
                "summary": c.summary,
                "primary": c.primary,
                "access_role": c.access_role,
            }
            for c in calendars
        ],
    }


@router.post("/availability")
async def check_availability(
    emails: list[str],
    provider: Literal["google", "outlook"] = Query("google"),
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    token: str | None = None,
):
    """Check free/busy availability for multiple users"""
    if not token:
        raise HTTPException(status_code=401, detail="Calendar token required")

    from ..integrations.calendar import (
        GoogleCalendarService,
        OutlookCalendarService,
        CalendarConfig,
    )

    config = CalendarConfig(provider=provider, token=token)

    if provider == "google":
        service = GoogleCalendarService(config)
    else:
        service = OutlookCalendarService(config)

    await service.initialize()

    if not time_min:
        time_min = datetime.now()
    if not time_max:
        time_max = time_min + timedelta(days=7)

    results = await service.get_free_busy(emails, time_min, time_max)

    return {
        "success": True,
        "results": [
            {
                "email": r.email,
                "busy": r.busy,
                "event_count": len(r.events),
            }
            for r in results
        ],
    }
