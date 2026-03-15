"""
Web Browser Tool - Web scraping and HTML parsing
"""
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

from .base import BaseTool, ToolResult, ToolParameter, ToolCategory, ToolRiskLevel


class WebBrowserTool(BaseTool):
    """
    Tool for web scraping and HTML parsing.
    Fetches web pages and extracts content using CSS selectors or text extraction.
    """
    
    name = "web_browser"
    description = (
        "Fetch and parse web pages. "
        "Can extract text content, follow links, and parse HTML using CSS selectors. "
        "Use for reading documentation, searching information, or extracting data from websites."
    )
    category = ToolCategory.WEB
    risk_level = ToolRiskLevel.NORMAL
    
    # Maximum page size (5MB)
    MAX_PAGE_SIZE = 5 * 1024 * 1024
    
    # Default timeout
    DEFAULT_TIMEOUT = 30
    
    def _get_parameters_schema(self) -> Dict[str, ToolParameter]:
        return {
            "url": ToolParameter(
                name="url",
                type="string",
                description="URL to fetch",
                required=True,
            ),
            "selector": ToolParameter(
                name="selector",
                type="string",
                description="CSS selector to extract specific elements (optional). Examples: 'article', '.content', '#main'",
                required=False,
            ),
            "extract_text": ToolParameter(
                name="extract_text",
                type="boolean",
                description="Extract clean text content (removes HTML tags)",
                required=False,
                default=True,
            ),
            "follow_links": ToolParameter(
                name="follow_links",
                type="boolean",
                description="Extract all links from the page",
                required=False,
                default=False,
            ),
            "max_length": ToolParameter(
                name="max_length",
                type="integer",
                description="Maximum characters to return (default 10000)",
                required=False,
                default=10000,
            ),
            "timeout": ToolParameter(
                name="timeout",
                type="integer",
                description="Request timeout in seconds",
                required=False,
                default=self.DEFAULT_TIMEOUT,
            ),
        }
    
    def _validate_config(self) -> None:
        """Validate tool configuration"""
        # Allowed domains (if empty, allow all except blocked)
        self.allowed_domains = self.config.get("allowed_domains", [])
        
        # Blocked domains
        self.blocked_domains = self.config.get("blocked_domains", [])
        
        # User agent
        self.user_agent = self.config.get(
            "user_agent",
            "Mozilla/5.0 (compatible; Qubot-Bot/1.0)",
        )
        
        # Respect robots.txt
        self.respect_robots = self.config.get("respect_robots", True)
    
    def _is_url_allowed(self, url: str) -> tuple[bool, Optional[str]]:
        """Check if URL is allowed"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www prefix for comparison
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check blocked
        if domain in self.blocked_domains:
            return False, f"Domain {domain} is blocked"
        
        # Check allowed
        if self.allowed_domains:
            allowed = False
            for allowed_domain in self.allowed_domains:
                if domain == allowed_domain or domain.endswith('.' + allowed_domain):
                    allowed = True
                    break
            if not allowed:
                return False, f"Domain {domain} not in allowed list"
        
        # Protocol check
        if parsed.scheme not in ('http', 'https'):
            return False, f"Unsupported protocol: {parsed.scheme}"
        
        return True, None
    
    async def execute(
        self,
        url: str,
        selector: Optional[str] = None,
        extract_text: bool = True,
        follow_links: bool = False,
        max_length: int = 10000,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> ToolResult:
        """
        Fetch and parse web page.
        
        Args:
            url: URL to fetch
            selector: CSS selector for specific elements
            extract_text: Extract clean text
            follow_links: Extract all links
            max_length: Max characters to return
            timeout: Request timeout
            
        Returns:
            ToolResult with extracted content
        """
        start_time = time.time()
        
        # Validate URL
        is_allowed, error = self._is_url_allowed(url)
        if not is_allowed:
            return ToolResult(
                success=False,
                error=f"URL not allowed: {error}",
            )
        
        try:
            import aiohttp
            from bs4 import BeautifulSoup
        except ImportError as e:
            return ToolResult(
                success=False,
                error=f"Required dependency not installed: {e.name}. Install with: pip install aiohttp beautifulsoup4",
            )
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            error=f"HTTP {response.status}: {response.reason}",
                            metadata={"status_code": response.status},
                        )
                    
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                        return ToolResult(
                            success=False,
                            error=f"Unsupported content type: {content_type}",
                        )
                    
                    # Read content
                    text = await response.text()
                    
                    if len(text) > self.MAX_PAGE_SIZE:
                        return ToolResult(
                            success=False,
                            error=f"Page too large (max {self.MAX_PAGE_SIZE} bytes)",
                        )
                    
                    # Parse HTML
                    soup = BeautifulSoup(text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.decompose()
                    
                    result_data = {
                        "url": str(response.url),
                        "title": soup.title.string if soup.title else None,
                    }
                    
                    # Extract content based on selector
                    if selector:
                        elements = soup.select(selector)
                        if not elements:
                            return ToolResult(
                                success=False,
                                error=f"No elements found matching selector: {selector}",
                                data=result_data,
                            )
                        
                        if extract_text:
                            content = "\n\n".join(el.get_text(strip=True) for el in elements)
                        else:
                            content = "\n\n".join(str(el) for el in elements)
                        
                        result_data["selected_elements"] = len(elements)
                    else:
                        # Extract main content
                        if extract_text:
                            # Try to find main content area
                            main = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.find('div', id='content')
                            if main:
                                content = main.get_text(separator='\n', strip=True)
                            else:
                                content = soup.get_text(separator='\n', strip=True)
                        else:
                            content = str(soup.find('body') or soup)
                    
                    # Truncate
                    if len(content) > max_length:
                        content = content[:max_length] + "\n\n[Content truncated...]"
                    
                    result_data["content"] = content
                    result_data["content_length"] = len(content)
                    
                    # Extract links if requested
                    if follow_links:
                        links = []
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            full_url = urljoin(str(response.url), href)
                            links.append({
                                "url": full_url,
                                "text": link.get_text(strip=True)[:100],
                            })
                        result_data["links"] = links[:100]  # Limit links
                    
                    # Extract meta tags
                    meta_tags = {}
                    for meta in soup.find_all('meta'):
                        name = meta.get('name') or meta.get('property')
                        content = meta.get('content')
                        if name and content:
                            meta_tags[name] = content
                    if meta_tags:
                        result_data["meta_tags"] = meta_tags
                    
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    return ToolResult(
                        success=True,
                        data=result_data,
                        stdout=content if extract_text else None,
                        execution_time_ms=execution_time,
                        metadata={
                            "status_code": response.status,
                            "content_type": content_type,
                            "page_size": len(text),
                            "selector": selector,
                        },
                    )
                    
        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                error=f"HTTP error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error fetching page: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
