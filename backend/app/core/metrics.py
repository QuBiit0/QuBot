"""
Prometheus metrics for monitoring
"""

import time

from fastapi import Request
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

# HTTP Request metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"],
)

# Business metrics
active_agents = Gauge("qubot_active_agents", "Number of active agents", ["status"])

tasks_total = Counter(
    "qubot_tasks_total", "Total tasks processed", ["status", "domain"]
)

task_duration_seconds = Histogram(
    "qubot_task_duration_seconds",
    "Task execution duration in seconds",
    ["domain"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
)

llm_calls_total = Counter(
    "qubot_llm_calls_total", "Total LLM API calls", ["provider", "model", "status"]
)

llm_tokens_total = Counter(
    "qubot_llm_tokens_total",
    "Total tokens used",
    ["provider", "type"],  # type: input/output
)

llm_cost_dollars = Counter(
    "qubot_llm_cost_dollars", "Total LLM cost in dollars", ["provider", "model"]
)

# WebSocket metrics
websocket_connections = Gauge(
    "qubot_websocket_connections", "Number of active WebSocket connections"
)

websocket_messages_total = Counter(
    "qubot_websocket_messages_total",
    "Total WebSocket messages",
    ["direction", "type"],  # direction: in/out
)

# Database metrics
db_connections_active = Gauge(
    "qubot_db_connections_active", "Number of active database connections"
)

db_query_duration_seconds = Histogram(
    "qubot_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for HTTP requests"""

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=path).inc()

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception as e:
            status_code = "500"
            raise e
        finally:
            # Record duration
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=path).observe(
                duration
            )

            # Record total requests
            http_requests_total.labels(
                method=method, endpoint=path, status_code=status_code
            ).inc()

            # Decrease in-progress
            http_requests_in_progress.labels(method=method, endpoint=path).dec()

        return response


def get_metrics():
    """Generate Prometheus metrics output"""
    return generate_latest()


# Helper functions to update metrics
def record_task_completed(domain: str, duration: float, status: str = "success"):
    """Record task completion metrics"""
    tasks_total.labels(status=status, domain=domain).inc()
    task_duration_seconds.labels(domain=domain).observe(duration)


def record_llm_call(provider: str, model: str, status: str = "success"):
    """Record LLM API call"""
    llm_calls_total.labels(provider=provider, model=model, status=status).inc()


def record_llm_tokens(provider: str, input_tokens: int, output_tokens: int):
    """Record token usage"""
    llm_tokens_total.labels(provider=provider, type="input").inc(input_tokens)
    llm_tokens_total.labels(provider=provider, type="output").inc(output_tokens)


def record_llm_cost(provider: str, model: str, cost: float):
    """Record LLM cost"""
    llm_cost_dollars.labels(provider=provider, model=model).inc(cost)


def update_active_agents(status: str, count: int):
    """Update active agents gauge"""
    active_agents.labels(status=status).set(count)


def record_websocket_message(direction: str, msg_type: str):
    """Record WebSocket message"""
    websocket_messages_total.labels(direction=direction, type=msg_type).inc()


def set_websocket_connections(count: int):
    """Set WebSocket connection count"""
    websocket_connections.set(count)


def record_db_query(operation: str, duration: float):
    """Record database query duration"""
    db_query_duration_seconds.labels(operation=operation).observe(duration)
