"""
Unit tests for TaskWorker — retry logic and dead-letter queue
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


def make_worker():
    """Create a TaskWorker with a mocked Redis connection."""
    with patch("app.worker.REDIS_AVAILABLE", True):
        from app.worker import TaskWorker
        worker = TaskWorker.__new__(TaskWorker)
        worker.redis = AsyncMock()
        worker.running = True
        worker.CONSUMER_NAME = "test-worker"
        worker._shutdown_event = MagicMock()
        worker._tasks = set()
        return worker


class TestHandleRetry:
    @pytest.mark.asyncio
    async def test_first_retry_increments_counter(self):
        worker = make_worker()
        # hincrby returns 1 (first retry)
        worker.redis.hincrby = AsyncMock(return_value=1)
        worker.redis.xadd = AsyncMock()
        worker.redis.xack = AsyncMock()
        worker.redis.hdel = AsyncMock()

        msg_id = b"1234-0"
        data = {"task_id": str(uuid4())}

        await worker._handle_retry(msg_id, data, "error message")

        # Should increment counter
        worker.redis.hincrby.assert_awaited_once_with(
            worker.RETRY_HASH, "1234-0", 1
        )
        # Should NOT yet send to dead-letter (only 1 of 3 retries)
        worker.redis.xadd.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_max_retries_sends_to_dead_letter(self):
        worker = make_worker()
        # hincrby returns MAX_RETRIES (3)
        worker.redis.hincrby = AsyncMock(return_value=worker.MAX_RETRIES)
        worker.redis.xadd = AsyncMock()
        worker.redis.xack = AsyncMock()
        worker.redis.hdel = AsyncMock()

        msg_id = b"5678-0"
        task_id = str(uuid4())
        data = {"task_id": task_id}

        await worker._handle_retry(msg_id, data, "terminal error")

        # Must write to dead-letter stream
        worker.redis.xadd.assert_awaited_once()
        dead_data = worker.redis.xadd.call_args.args[1]
        assert dead_data["task_id"] == task_id
        assert dead_data["error"] == "terminal error"
        assert "dead_at" in dead_data

        # Must ack the original message
        worker.redis.xack.assert_awaited_once()

        # Must clean up retry counter
        worker.redis.hdel.assert_awaited_once_with(worker.RETRY_HASH, "5678-0")

    @pytest.mark.asyncio
    async def test_second_retry_does_not_dead_letter(self):
        worker = make_worker()
        worker.redis.hincrby = AsyncMock(return_value=2)
        worker.redis.xadd = AsyncMock()
        worker.redis.xack = AsyncMock()
        worker.redis.hdel = AsyncMock()

        await worker._handle_retry(b"9999-0", {"task_id": "x"}, "err")

        worker.redis.xadd.assert_not_awaited()
        worker.redis.xack.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_retry_handles_string_msg_id(self):
        """msg_id may be str instead of bytes"""
        worker = make_worker()
        worker.redis.hincrby = AsyncMock(return_value=1)
        worker.redis.xadd = AsyncMock()
        worker.redis.xack = AsyncMock()
        worker.redis.hdel = AsyncMock()

        await worker._handle_retry("1234-0", {"task_id": "abc"}, "err")

        worker.redis.hincrby.assert_awaited_once_with(
            worker.RETRY_HASH, "1234-0", 1
        )

    @pytest.mark.asyncio
    async def test_retry_handles_redis_error_gracefully(self):
        """Redis failure during retry should not propagate as exception"""
        worker = make_worker()
        worker.redis.hincrby = AsyncMock(side_effect=Exception("Redis down"))

        # Should not raise
        await worker._handle_retry(b"fail-0", {}, "err")


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_missing_task_id_acks_message(self):
        worker = make_worker()
        worker._ack_message = AsyncMock()
        worker._execute_task = AsyncMock()

        msg_id = b"111-0"
        fields = {b"other_field": b"value"}  # No task_id

        await worker._process_message((msg_id, fields))

        worker._ack_message.assert_awaited_once_with(msg_id)
        worker._execute_task.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_successful_execution_acks_message(self):
        worker = make_worker()
        task_id = str(uuid4())
        worker._ack_message = AsyncMock()
        worker._execute_task = AsyncMock(return_value={"success": True})
        worker._handle_retry = AsyncMock()

        msg_id = b"222-0"
        fields = {b"task_id": task_id.encode()}

        await worker._process_message((msg_id, fields))

        worker._execute_task.assert_awaited_once()
        worker._ack_message.assert_awaited_once_with(msg_id)
        worker._handle_retry.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_failed_execution_still_acks(self):
        worker = make_worker()
        task_id = str(uuid4())
        worker._ack_message = AsyncMock()
        worker._execute_task = AsyncMock(return_value={"success": False, "error": "oops"})
        worker._handle_retry = AsyncMock()

        await worker._process_message((b"333-0", {b"task_id": task_id.encode()}))

        # Ack even on failure (retry handled separately by _handle_retry on exception)
        worker._ack_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_exception_triggers_retry(self):
        worker = make_worker()
        task_id = str(uuid4())
        worker._ack_message = AsyncMock()
        worker._execute_task = AsyncMock(side_effect=RuntimeError("crash"))
        worker._handle_retry = AsyncMock()

        await worker._process_message((b"444-0", {b"task_id": task_id.encode()}))

        worker._handle_retry.assert_awaited_once()
        # Should NOT ack when exception triggers retry
        worker._ack_message.assert_not_awaited()


class TestAckMessage:
    @pytest.mark.asyncio
    async def test_ack_calls_xack(self):
        worker = make_worker()
        worker.redis.xack = AsyncMock()

        await worker._ack_message(b"100-0")

        worker.redis.xack.assert_awaited_once_with(
            worker.TASK_STREAM,
            worker.TASK_GROUP,
            b"100-0",
        )

    @pytest.mark.asyncio
    async def test_ack_handles_redis_error(self):
        worker = make_worker()
        worker.redis.xack = AsyncMock(side_effect=Exception("Redis error"))

        # Should not raise
        await worker._ack_message(b"999-0")
