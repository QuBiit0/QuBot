"""
HTTP API Tool - Make HTTP requests to external APIs
"""
import time
import json
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse
import aiohttp

from .base import BaseTool, ToolResult, ToolParameter, ToolCategory, ToolRiskLevel


class HttpApiTool(BaseTool):
    """
    Tool for making HTTP requests to external APIs.
    Supports GET, POST, PUT, DELETE with custom headers and auth.
    """
    
    name = "http_api"
    description = (
        "Make HTTP requests to external APIs. "
        "Supports various HTTP methods, custom headers, and authentication. "
        "Use for fetching data from web services or sending data to external systems."
    )
    category = ToolCategory.WEB
    risk_level = ToolRiskLevel.NORMAL
    
    # HTTP methods allowed
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    
    # Default timeout
    DEFAULT_TIMEOUT = 30
    
    # Maximum response size (10MB)
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024
    
    def _get_parameters_schema(self) -> Dict[str, ToolParameter]:
        return {
            "url": ToolParameter(
                name="url",
                type="string",
                description="The URL to make the request to",
                required=True,
            ),
            "method": ToolParameter(
                name="method",
                type="string",
                description="HTTP method to use",
                required=False,
                default="GET",
                enum=self.ALLOWED_METHODS,
            ),
            "headers": ToolParameter(
                name="headers",
                type="object",
                description="Custom HTTP headers as key-value pairs",
                required=False,
                default={},
            ),
            "body": ToolParameter(
                name="body",
                type="string",
                description="Request body (for POST/PUT/PATCH). Can be JSON string or raw text",
                required=False,
            ),
            "query_params": ToolParameter(
                name="query_params",
                type="object",
                description="Query parameters as key-value pairs",
                required=False,
                default={},
            ),
            "timeout": ToolParameter(
                name="timeout",
                type="integer",
                description="Request timeout in seconds (max 60)",
                required=False,
                default=self.DEFAULT_TIMEOUT,
            ),
        }
    
    def _validate_config(self) -> None:
        """Validate tool configuration"""
        # Check for allowed hosts (security)
        self.allowed_hosts = self.config.get("allowed_hosts", [])
        self.blocked_hosts = self.config.get("blocked_hosts", [
            "localhost", "127.0.0.1", "0.0.0.0",
            "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
        ])
        
        # Default headers from config
        self.default_headers = self.config.get("default_headers", {
            "User-Agent": "Qubot-HTTP-Tool/1.0",
        })
        
        # Authentication
        self.auth_header = self.config.get("auth_header")
        self.auth_token = self.config.get("auth_token")
    
    def _is_host_allowed(self, url: str) -> bool:
        """Check if host is allowed (security check)"""
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            return False
        
        # Check blocked hosts
        if hostname in self.blocked_hosts:
            return False
        
        # Check allowed hosts (if specified, only allow those)
        if self.allowed_hosts and hostname not in self.allowed_hosts:
            return False
        
        return True
    
    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        query_params: Optional[Dict[str, str]] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> ToolResult:
        """
        Execute HTTP request.
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Custom headers
            body: Request body
            query_params: URL query parameters
            timeout: Request timeout
            
        Returns:
            ToolResult with response data
        """
        start_time = time.time()
        
        # Validate URL
        if not url.startswith(("http://", "https://")):
            return ToolResult(
                success=False,
                error="URL must start with http:// or https://",
            )
        
        # Security check
        if not self._is_host_allowed(url):
            return ToolResult(
                success=False,
                error="Host not allowed for security reasons",
            )
        
        # Validate method
        method = method.upper()
        if method not in self.ALLOWED_METHODS:
            return ToolResult(
                success=False,
                error=f"Method {method} not allowed. Use: {', '.join(self.ALLOWED_METHODS)}",
            )
        
        # Build headers
        request_headers = dict(self.default_headers)
        if headers:
            request_headers.update(headers)
        
        # Add auth if configured
        if self.auth_header and self.auth_token:
            request_headers[self.auth_header] = self.auth_token
        
        # Cap timeout
        timeout = min(timeout, 60)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=query_params,
                    data=body,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    # Check response size
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) > self.MAX_RESPONSE_SIZE:
                        return ToolResult(
                            success=False,
                            error=f"Response too large (max {self.MAX_RESPONSE_SIZE} bytes)",
                            metadata={"status_code": response.status},
                        )
                    
                    # Read response
                    try:
                        text = await response.text()
                    except Exception as e:
                        return ToolResult(
                            success=False,
                            error=f"Failed to read response: {str(e)}",
                            metadata={"status_code": response.status},
                        )
                    
                    # Try to parse as JSON
                    data = None
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        data = text if len(text) < 10000 else text[:10000] + "... [truncated]"
                    
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    return ToolResult(
                        success=200 <= response.status < 300,
                        data={
                            "status_code": response.status,
                            "headers": dict(response.headers),
                            "body": data,
                            "url": str(response.url),
                        },
                        stdout=text if isinstance(data, str) else json.dumps(data, indent=2),
                        execution_time_ms=execution_time,
                        metadata={
                            "status_code": response.status,
                            "content_type": response.headers.get('Content-Type'),
                            "content_length": len(text),
                        },
                    )
                    
        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                error=f"HTTP client error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
