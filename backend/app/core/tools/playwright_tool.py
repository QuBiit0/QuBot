"""
Playwright Browser Tool - Full browser automation for JS-heavy sites
Handles SPAs, dynamic content, screenshots, form filling, and interactions.
"""

import time

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class PlaywrightBrowserTool(BaseTool):
    """
    Full browser automation using Playwright.
    Unlike web_browser, this tool renders JavaScript and handles dynamic content.
    Use for: SPAs, React/Vue/Angular sites, login flows, form submissions,
    content behind JS rendering, screenshots, and interactive workflows.
    """

    name = "browser_automation"
    description = (
        "Automate a real browser (Chromium) to interact with websites. "
        "Handles JavaScript-heavy pages, SPAs, and dynamic content. "
        "Can take screenshots, fill forms, click buttons, and extract rendered content. "
        "Use when web_browser fails or for interactive workflows."
    )
    category = ToolCategory.WEB
    risk_level = ToolRiskLevel.NORMAL

    DEFAULT_TIMEOUT = 30000  # ms

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "url": ToolParameter(
                name="url",
                type="string",
                description="URL to navigate to",
                required=True,
            ),
            "action": ToolParameter(
                name="action",
                type="string",
                description=(
                    "Action to perform: "
                    "'screenshot' (take screenshot), "
                    "'get_text' (extract visible text), "
                    "'get_html' (get page HTML after JS render), "
                    "'click' (click an element), "
                    "'fill' (fill a form field), "
                    "'wait_for' (wait for element to appear)"
                ),
                required=False,
                default="get_text",
                enum=["screenshot", "get_text", "get_html", "click", "fill", "wait_for"],
            ),
            "selector": ToolParameter(
                name="selector",
                type="string",
                description="CSS selector or XPath for element targeting (e.g. '#email', 'button[type=submit]')",
                required=False,
                default=None,
            ),
            "value": ToolParameter(
                name="value",
                type="string",
                description="Value to fill in form field (used with action='fill')",
                required=False,
                default=None,
            ),
            "wait_for_selector": ToolParameter(
                name="wait_for_selector",
                type="string",
                description="CSS selector to wait for before extracting content",
                required=False,
                default=None,
            ),
            "timeout": ToolParameter(
                name="timeout",
                type="integer",
                description="Timeout in milliseconds (default 30000)",
                required=False,
                default=30000,
            ),
            "headless": ToolParameter(
                name="headless",
                type="boolean",
                description="Run browser in headless mode (default True)",
                required=False,
                default=True,
            ),
            "max_length": ToolParameter(
                name="max_length",
                type="integer",
                description="Maximum characters for text extraction (default 15000)",
                required=False,
                default=15000,
            ),
        }

    def _validate_config(self) -> None:
        self.headless = self.config.get("headless", True)
        self.user_agent = self.config.get(
            "user_agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

    async def execute(
        self,
        url: str,
        action: str = "get_text",
        selector: str | None = None,
        value: str | None = None,
        wait_for_selector: str | None = None,
        timeout: int = 30000,
        headless: bool = True,
        max_length: int = 15000,
    ) -> ToolResult:
        """
        Automate a browser to interact with a webpage.

        Args:
            url: URL to navigate to
            action: Action to perform
            selector: CSS selector for element targeting
            value: Value for fill action
            wait_for_selector: CSS selector to wait for
            timeout: Timeout in ms
            headless: Run headless
            max_length: Max chars for text output

        Returns:
            ToolResult with extracted content, screenshot, or action result
        """
        start_time = time.time()

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return ToolResult(
                success=False,
                error=(
                    "playwright package not installed. "
                    "Install with: pip install playwright && playwright install chromium"
                ),
            )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1280, "height": 800},
                )
                page = await context.new_page()

                try:
                    # Navigate
                    await page.goto(url, timeout=timeout, wait_until="domcontentloaded")

                    # Wait for specific selector if requested
                    if wait_for_selector:
                        await page.wait_for_selector(wait_for_selector, timeout=timeout)

                    # Perform action
                    if action == "screenshot":
                        screenshot_bytes = await page.screenshot(full_page=True)
                        return ToolResult(
                            success=True,
                            data={
                                "url": page.url,
                                "title": await page.title(),
                                "screenshot_size": len(screenshot_bytes),
                                "screenshot_bytes": screenshot_bytes.hex(),
                            },
                            stdout=f"Screenshot taken for {page.url} ({len(screenshot_bytes)} bytes)",
                            execution_time_ms=int((time.time() - start_time) * 1000),
                        )

                    elif action == "get_text":
                        if selector:
                            elements = await page.query_selector_all(selector)
                            if not elements:
                                return ToolResult(
                                    success=False,
                                    error=f"No elements found matching: {selector}",
                                    execution_time_ms=int((time.time() - start_time) * 1000),
                                )
                            texts = []
                            for el in elements:
                                t = await el.inner_text()
                                if t.strip():
                                    texts.append(t.strip())
                            content = "\n\n".join(texts)
                        else:
                            content = await page.inner_text("body")

                        if len(content) > max_length:
                            content = content[:max_length] + "\n\n[Content truncated...]"

                        return ToolResult(
                            success=True,
                            data={
                                "url": page.url,
                                "title": await page.title(),
                                "content": content,
                                "content_length": len(content),
                            },
                            stdout=content,
                            execution_time_ms=int((time.time() - start_time) * 1000),
                        )

                    elif action == "get_html":
                        if selector:
                            el = await page.query_selector(selector)
                            if not el:
                                return ToolResult(
                                    success=False,
                                    error=f"Element not found: {selector}",
                                    execution_time_ms=int((time.time() - start_time) * 1000),
                                )
                            html = await el.inner_html()
                        else:
                            html = await page.content()

                        if len(html) > max_length:
                            html = html[:max_length] + "<!-- truncated -->"

                        return ToolResult(
                            success=True,
                            data={
                                "url": page.url,
                                "title": await page.title(),
                                "html": html,
                                "html_length": len(html),
                            },
                            stdout=html,
                            execution_time_ms=int((time.time() - start_time) * 1000),
                        )

                    elif action == "click":
                        if not selector:
                            return ToolResult(
                                success=False,
                                error="selector is required for action 'click'",
                            )
                        await page.click(selector, timeout=timeout)
                        # Wait for navigation/network to settle
                        await page.wait_for_load_state("networkidle", timeout=timeout)
                        return ToolResult(
                            success=True,
                            data={"url": page.url, "title": await page.title()},
                            stdout=f"Clicked '{selector}', now at: {page.url}",
                            execution_time_ms=int((time.time() - start_time) * 1000),
                        )

                    elif action == "fill":
                        if not selector:
                            return ToolResult(
                                success=False,
                                error="selector is required for action 'fill'",
                            )
                        if value is None:
                            return ToolResult(
                                success=False,
                                error="value is required for action 'fill'",
                            )
                        await page.fill(selector, value, timeout=timeout)
                        return ToolResult(
                            success=True,
                            data={"selector": selector, "value": "***" if "password" in selector.lower() else value},
                            stdout=f"Filled field '{selector}'",
                            execution_time_ms=int((time.time() - start_time) * 1000),
                        )

                    elif action == "wait_for":
                        if not selector:
                            return ToolResult(
                                success=False,
                                error="selector is required for action 'wait_for'",
                            )
                        await page.wait_for_selector(selector, timeout=timeout)
                        el = await page.query_selector(selector)
                        text = await el.inner_text() if el else ""
                        return ToolResult(
                            success=True,
                            data={"selector": selector, "found": True, "text": text},
                            stdout=f"Element '{selector}' appeared: {text}",
                            execution_time_ms=int((time.time() - start_time) * 1000),
                        )

                    else:
                        return ToolResult(
                            success=False,
                            error=f"Unknown action: {action}",
                        )

                finally:
                    await browser.close()

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Browser automation failed: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
