"""
Email Tool - Send and read emails via SMTP/IMAP.
Gives agents the ability to communicate asynchronously with the outside world.
"""

import time

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class EmailTool(BaseTool):
    """
    Send emails via SMTP and read/search emails via IMAP.
    Configure via environment variables:
      EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD
      EMAIL_IMAP_HOST, EMAIL_IMAP_PORT, EMAIL_IMAP_USER, EMAIL_IMAP_PASSWORD

    Operations:
    - send: Send an email with optional attachments
    - read: Read recent emails from inbox
    - search: Search emails by subject/sender/body
    """

    name = "email"
    description = (
        "Send and read emails. "
        "Use 'send' to send emails with subject, body (HTML or plain text), and optional attachments. "
        "Use 'read' to fetch recent inbox emails. "
        "Use 'search' to find emails matching a query. "
        "Requires SMTP/IMAP configuration in environment variables."
    )
    category = ToolCategory.COMMUNICATION
    risk_level = ToolRiskLevel.NORMAL

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'send', 'read', 'search'",
                required=True,
                enum=["send", "read", "search"],
            ),
            "to": ToolParameter(
                name="to",
                type="string",
                description="Recipient email address(es), comma-separated (for 'send')",
                required=False,
                default=None,
            ),
            "subject": ToolParameter(
                name="subject",
                type="string",
                description="Email subject (for 'send')",
                required=False,
                default=None,
            ),
            "body": ToolParameter(
                name="body",
                type="string",
                description="Email body (plain text or HTML)",
                required=False,
                default=None,
            ),
            "html": ToolParameter(
                name="html",
                type="boolean",
                description="Treat body as HTML (default False)",
                required=False,
                default=False,
            ),
            "cc": ToolParameter(
                name="cc",
                type="string",
                description="CC recipients, comma-separated",
                required=False,
                default=None,
            ),
            "reply_to": ToolParameter(
                name="reply_to",
                type="string",
                description="Reply-To address",
                required=False,
                default=None,
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="IMAP search query, e.g. 'FROM user@example.com', 'SUBJECT report', 'UNSEEN'",
                required=False,
                default="UNSEEN",
            ),
            "folder": ToolParameter(
                name="folder",
                type="string",
                description="IMAP folder to search/read (default: INBOX)",
                required=False,
                default="INBOX",
            ),
            "max_emails": ToolParameter(
                name="max_emails",
                type="integer",
                description="Maximum emails to return for read/search (default 10, max 50)",
                required=False,
                default=10,
            ),
            "mark_read": ToolParameter(
                name="mark_read",
                type="boolean",
                description="Mark fetched emails as read (default False)",
                required=False,
                default=False,
            ),
        }

    def _validate_config(self) -> None:
        import os
        self.smtp_host = self.config.get("smtp_host") or os.getenv("EMAIL_SMTP_HOST", "")
        self.smtp_port = int(self.config.get("smtp_port") or os.getenv("EMAIL_SMTP_PORT", "587"))
        self.smtp_user = self.config.get("smtp_user") or os.getenv("EMAIL_SMTP_USER", "")
        self.smtp_pass = self.config.get("smtp_password") or os.getenv("EMAIL_SMTP_PASSWORD", "")
        self.smtp_tls = self.config.get("smtp_tls", True)

        self.imap_host = self.config.get("imap_host") or os.getenv("EMAIL_IMAP_HOST", "")
        self.imap_port = int(self.config.get("imap_port") or os.getenv("EMAIL_IMAP_PORT", "993"))
        self.imap_user = self.config.get("imap_user") or os.getenv("EMAIL_IMAP_USER", self.smtp_user)
        self.imap_pass = self.config.get("imap_password") or os.getenv("EMAIL_IMAP_PASSWORD", self.smtp_pass)
        self.from_addr = self.config.get("from_address") or self.smtp_user

    async def _send(self, to: str, subject: str, body: str, html: bool,
                    cc: str | None, reply_to: str | None) -> ToolResult:
        if not self.smtp_host or not self.smtp_user:
            return ToolResult(
                success=False,
                error="SMTP not configured. Set EMAIL_SMTP_HOST, EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD.",
            )

        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
        except ImportError:
            return ToolResult(success=False, error="aiosmtplib not installed: pip install aiosmtplib")

        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject or "(no subject)"
        if cc:
            msg["Cc"] = cc
        if reply_to:
            msg["Reply-To"] = reply_to

        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body or "", mime_type, "utf-8"))

        recipients = [a.strip() for a in to.split(",")]
        if cc:
            recipients += [a.strip() for a in cc.split(",")]

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_pass,
                start_tls=self.smtp_port == 587,
                use_tls=self.smtp_port == 465,
                timeout=30,
            )
            return ToolResult(
                success=True,
                data={"sent_to": recipients, "subject": subject},
                stdout=f"Email sent to {', '.join(recipients)}: {subject}",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"SMTP send failed: {e}")

    async def _read_imap(self, query: str, folder: str, max_emails: int, mark_read: bool) -> ToolResult:
        if not self.imap_host or not self.imap_user:
            return ToolResult(
                success=False,
                error="IMAP not configured. Set EMAIL_IMAP_HOST, EMAIL_IMAP_USER, EMAIL_IMAP_PASSWORD.",
            )

        import asyncio
        import imaplib
        import email as email_lib
        from email.header import decode_header

        def _decode_header_value(val: str | bytes | None) -> str:
            if val is None:
                return ""
            if isinstance(val, bytes):
                parts = decode_header(val.decode("utf-8", errors="replace"))
            else:
                parts = decode_header(val)
            decoded = []
            for part, enc in parts:
                if isinstance(part, bytes):
                    decoded.append(part.decode(enc or "utf-8", errors="replace"))
                else:
                    decoded.append(str(part))
            return " ".join(decoded)

        def _fetch_emails():
            conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            conn.login(self.imap_user, self.imap_pass)
            conn.select(folder)

            # Build IMAP search criteria
            criteria = query.upper() if query else "ALL"
            _, msg_ids = conn.search(None, criteria)
            ids = msg_ids[0].split()
            ids = ids[-max_emails:]  # take last N

            emails = []
            for mid in reversed(ids):
                _, data = conn.fetch(mid, "(RFC822)")
                if data and data[0]:
                    raw = data[0][1]
                    msg = email_lib.message_from_bytes(raw)
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain" and not part.get_filename():
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode("utf-8", errors="replace")[:1000]
                                    break
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode("utf-8", errors="replace")[:1000]

                    if mark_read:
                        conn.store(mid, "+FLAGS", "\\Seen")

                    emails.append({
                        "id": mid.decode(),
                        "from": _decode_header_value(msg.get("From")),
                        "to": _decode_header_value(msg.get("To")),
                        "subject": _decode_header_value(msg.get("Subject")),
                        "date": msg.get("Date", ""),
                        "body": body,
                    })

            conn.logout()
            return emails

        try:
            emails = await asyncio.get_event_loop().run_in_executor(None, _fetch_emails)
            lines = [f"Emails from {folder} ({len(emails)}):\n"]
            for e in emails:
                lines.append(f"From: {e['from']}")
                lines.append(f"Subject: {e['subject']}")
                lines.append(f"Date: {e['date']}")
                lines.append(f"Body: {e['body'][:200]}\n")

            return ToolResult(
                success=True,
                data={"emails": emails, "count": len(emails), "folder": folder},
                stdout="\n".join(lines),
            )
        except Exception as e:
            return ToolResult(success=False, error=f"IMAP read failed: {e}")

    async def execute(
        self,
        operation: str,
        to: str | None = None,
        subject: str | None = None,
        body: str | None = None,
        html: bool = False,
        cc: str | None = None,
        reply_to: str | None = None,
        query: str = "UNSEEN",
        folder: str = "INBOX",
        max_emails: int = 10,
        mark_read: bool = False,
    ) -> ToolResult:
        start_time = time.time()
        max_emails = min(max(1, max_emails), 50)

        try:
            if operation == "send":
                if not to:
                    return ToolResult(success=False, error="'to' is required for send operation")
                result = await self._send(to, subject or "(no subject)", body or "", html, cc, reply_to)
            elif operation in ("read", "search"):
                result = await self._read_imap(query, folder, max_emails, mark_read)
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")

            result.execution_time_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Email operation failed: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
