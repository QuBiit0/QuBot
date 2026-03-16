"""
Qubot Worker - Background task processor using Redis Streams

The worker processes tasks asynchronously from Redis Streams.
Multiple workers can run in parallel for scalability.
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


from .config import settings
from .database import AsyncSessionLocal
from .services.execution_service import ExecutionService

logger = structlog.get_logger(__name__)


class TaskWorker:
    """
    Worker that processes tasks from Redis Streams.

    Features:
    - Claim pending messages (handles crashed workers)
    - Acknowledge completed tasks
    - Heartbeat to track worker health
    - Graceful shutdown
    """

    # Redis stream keys
    TASK_STREAM = "qubot:tasks:stream"
    TASK_GROUP = "qubot:workers"
    WORKER_HEARTBEAT = "qubot:workers:heartbeat"
    DEAD_LETTER_STREAM = "qubot:tasks:dead"
    RETRY_HASH = "qubot:tasks:retries"

    # Consumer configuration
    CONSUMER_NAME: str | None = None
    BLOCK_TIMEOUT = 5000  # ms to wait for new messages
    CLAIM_INTERVAL = 30  # seconds between claiming pending messages
    HEARTBEAT_INTERVAL = 10  # seconds between heartbeats
    MAX_RETRIES = 3  # max retries before dead-letter

    def __init__(self):
        self.redis = None
        self.running = False
        self._shutdown_event = asyncio.Event()
        self._tasks: set = set()

        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is required for worker. Install with: pip install redis"
            )

    async def start(self, consumer_name: str | None = None):
        """Start the worker"""
        self.CONSUMER_NAME = consumer_name or f"worker-{datetime.utcnow().timestamp()}"

        logger.info("worker_start", consumer=self.CONSUMER_NAME)

        # Connect to Redis
        self.redis = redis.from_url(settings.REDIS_URL)

        # Ensure consumer group exists
        await self._create_consumer_group()

        # Set up signal handlers
        self._setup_signals()

        self.running = True

        # Start background tasks
        self._tasks.add(asyncio.create_task(self._heartbeat_loop()))
        self._tasks.add(asyncio.create_task(self._claim_pending_loop()))

        # Main processing loop
        try:
            await self._process_loop()
        except asyncio.CancelledError:
            logger.info("worker_cancelled")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("worker_shutdown_start")
        self.running = False
        self._shutdown_event.set()

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Remove from heartbeat
        if self.redis and self.CONSUMER_NAME:
            await self.redis.hdel(self.WORKER_HEARTBEAT, self.CONSUMER_NAME)

        # Close Redis connection
        if self.redis:
            await self.redis.close()

        logger.info("worker_shutdown_complete")

    def _setup_signals(self):
        """Set up signal handlers for graceful shutdown"""

        def signal_handler(sig, frame):
            logger.info("signal_received", signal=sig)
            asyncio.create_task(self.shutdown())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _create_consumer_group(self):
        """Create Redis consumer group if it doesn't exist"""
        try:
            await self.redis.xgroup_create(
                self.TASK_STREAM,
                self.TASK_GROUP,
                id="0",  # From beginning
                mkstream=True,
            )
            logger.info("consumer_group_created", group=self.TASK_GROUP)
        except redis.ResponseError as e:
            if "already exists" in str(e):
                logger.info("consumer_group_exists", group=self.TASK_GROUP)
            else:
                raise

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                await self.redis.hset(
                    self.WORKER_HEARTBEAT,
                    self.CONSUMER_NAME,
                    json.dumps(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "status": "active",
                        }
                    ),
                )
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.error("heartbeat_error", error=str(e))
                await asyncio.sleep(1)

    async def _claim_pending_loop(self):
        """Periodically claim pending messages from other workers"""
        while self.running:
            try:
                await self._claim_pending_messages()
                await asyncio.sleep(self.CLAIM_INTERVAL)
            except Exception as e:
                logger.error("claim_pending_error", error=str(e))
                await asyncio.sleep(1)

    async def _claim_pending_messages(self):
        """Claim pending messages that may be stuck"""
        # Get pending messages
        pending = await self.redis.xpending(
            self.TASK_STREAM,
            self.TASK_GROUP,
        )

        if not pending or pending.get("pending", 0) == 0:
            return

        logger.debug("pending_messages_found", count=pending['pending'])

        # Claim messages idle for more than 60 seconds
        claimed = await self.redis.xautoclaim(
            self.TASK_STREAM,
            self.TASK_GROUP,
            self.CONSUMER_NAME,
            min_idle_time=60000,  # 60 seconds
            count=10,
        )

        if claimed and claimed[1]:  # claimed[1] is the list of messages
            logger.info("claimed_pending_messages", count=len(claimed[1]))
            for message in claimed[1]:
                await self._process_message(message)

    async def _process_loop(self):
        """Main message processing loop"""
        while self.running:
            try:
                # Read new messages
                messages = await self.redis.xreadgroup(
                    groupname=self.TASK_GROUP,
                    consumername=self.CONSUMER_NAME,
                    streams={self.TASK_STREAM: ">"},  # Undelivered messages
                    count=1,
                    block=self.BLOCK_TIMEOUT,
                )

                if not messages:
                    continue

                # Process each message
                for _stream, msgs in messages:
                    for msg_id, fields in msgs:
                        await self._process_message((msg_id, fields))

            except Exception as e:
                logger.error("processing_loop_error", error=str(e))
                await asyncio.sleep(1)

    async def _process_message(self, message: tuple):
        """Process a single task message"""
        msg_id, fields = message

        try:
            # Parse message
            data = {
                k.decode() if isinstance(k, bytes) else k: v.decode()
                if isinstance(v, bytes)
                else v
                for k, v in fields.items()
            }

            task_id = data.get("task_id")
            if not task_id:
                logger.error("message_missing_task_id", data=str(data))
                await self._ack_message(msg_id)
                return

            logger.info("processing_task", task_id=str(task_id))

            # Execute task
            result = await self._execute_task(UUID(task_id))

            if result.get("success"):
                logger.info("task_completed", task_id=str(task_id))
            else:
                logger.error("task_failed", task_id=str(task_id), error=result.get('error'))

            # Acknowledge message
            await self._ack_message(msg_id)

        except Exception as e:
            logger.error("message_processing_error", msg_id=str(msg_id), error=str(e))
            await self._handle_retry(msg_id, data if "data" in dir() else {}, str(e))

    async def _execute_task(self, task_id: UUID) -> dict[str, Any]:
        """Execute a task using the execution service"""
        async with AsyncSessionLocal() as session:
            try:
                execution_service = ExecutionService(session)

                result = await execution_service.execute_task(
                    task_id=task_id,
                    max_iterations=10,
                )

                await session.commit()
                return result

            except Exception as e:
                await session.rollback()
                logger.error("task_execution_error", error=str(e))
                return {"success": False, "error": str(e)}

    async def _ack_message(self, msg_id: bytes):
        """Acknowledge message as processed"""
        try:
            await self.redis.xack(
                self.TASK_STREAM,
                self.TASK_GROUP,
                msg_id,
            )
        except Exception as e:
            logger.error("ack_error", error=str(e))

    async def _handle_retry(self, msg_id: bytes, data: dict, error: str):
        """Handle retry logic with dead-letter queue"""
        try:
            msg_key = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
            retry_count = await self.redis.hincrby(self.RETRY_HASH, msg_key, 1)

            if retry_count >= self.MAX_RETRIES:
                # Move to dead-letter stream
                dead_data = {
                    "original_msg_id": msg_key,
                    "task_id": data.get("task_id", "unknown"),
                    "error": error,
                    "retries": str(retry_count),
                    "dead_at": datetime.utcnow().isoformat(),
                }
                await self.redis.xadd(self.DEAD_LETTER_STREAM, dead_data)
                await self._ack_message(msg_id)
                await self.redis.hdel(self.RETRY_HASH, msg_key)
                logger.warning(
                    "task_dead_lettered",
                    task_id=data.get("task_id"),
                    retries=retry_count,
                )
            else:
                logger.info(
                    "task_retry",
                    task_id=data.get("task_id"),
                    attempt=retry_count,
                    max_retries=self.MAX_RETRIES,
                )
        except Exception as e:
            logger.error("retry_handling_error", msg_id=str(msg_id), error=str(e))


class TaskQueue:
    """Client for submitting tasks to the queue"""

    TASK_STREAM = "qubot:tasks:stream"

    def __init__(self):
        self.redis = None

        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is required for TaskQueue. Install with: pip install redis"
            )

    async def connect(self):
        """Connect to Redis"""
        self.redis = redis.from_url(settings.REDIS_URL)

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()

    async def submit_task(
        self,
        task_id: UUID,
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Submit a task to the queue.

        Args:
            task_id: Task ID to execute
            priority: Task priority (higher = more important)
            metadata: Optional metadata

        Returns:
            Message ID
        """
        if not self.redis:
            await self.connect()

        message = {
            "task_id": str(task_id),
            "priority": str(priority),
            "submitted_at": datetime.utcnow().isoformat(),
        }

        if metadata:
            message["metadata"] = json.dumps(metadata)

        # Add to stream
        msg_id = await self.redis.xadd(
            self.TASK_STREAM,
            message,
        )

        logger.info("task_submitted", task_id=str(task_id), msg_id=str(msg_id))
        return msg_id

    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics"""
        if not self.redis:
            await self.connect()

        # Get stream length
        length = await self.redis.xlen(self.TASK_STREAM)

        # Get pending count
        try:
            pending = await self.redis.xpending(
                self.TASK_STREAM,
                "qubot:workers",
            )
            pending_count = pending.get("pending", 0)
        except Exception:
            pending_count = 0

        # Get worker heartbeats
        workers = await self.redis.hgetall("qubot:workers:heartbeat")
        active_workers = len(workers)

        return {
            "stream_length": length,
            "pending_messages": pending_count,
            "active_workers": active_workers,
            "workers": [
                json.loads(w.decode() if isinstance(w, bytes) else w)
                for w in workers.values()
            ]
            if workers
            else [],
        }


# Convenience functions for running worker
async def run_worker(consumer_name: str | None = None):
    """Run a worker process"""
    worker = TaskWorker()
    await worker.start(consumer_name)


async def submit_task_to_queue(
    task_id: UUID,
    priority: int = 0,
) -> str:
    """Submit a task to the processing queue"""
    queue = TaskQueue()
    await queue.connect()

    try:
        msg_id = await queue.submit_task(task_id, priority)
        return msg_id
    finally:
        await queue.disconnect()


if __name__ == "__main__":
    # Run worker when called directly
    import sys

    consumer_name = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        asyncio.run(run_worker(consumer_name))
    except KeyboardInterrupt:
        logger.info("worker_stopped_by_user")
