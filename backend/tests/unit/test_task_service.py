"""
Unit tests for TaskService — CRUD, status transitions, and event creation
"""

from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

import pytest

from app.models.enums import PriorityEnum, TaskEventTypeEnum, TaskStatusEnum
from app.models.task import Task, TaskEvent
from app.services.task_service import TaskService


def make_mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


def make_task(**kwargs) -> MagicMock:
    defaults = dict(
        id=uuid4(),
        title="Test Task",
        description="A task for testing",
        status=TaskStatusEnum.BACKLOG,
        priority=PriorityEnum.MEDIUM,
        domain_hint=None,
        assigned_agent_id=None,
        parent_task_id=None,
        completed_at=None,
    )
    defaults.update(kwargs)
    t = MagicMock(spec=Task)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


class TestTaskServiceCreate:
    @pytest.mark.asyncio
    async def test_create_task_minimal(self):
        session = make_mock_session()
        service = TaskService(session)
        session.refresh.side_effect = lambda obj: None

        with patch("app.services.task_service.Task") as MockTask, \
             patch.object(service, "create_task_event", new_callable=AsyncMock):
            mock_task = make_task(title="Buy milk")
            MockTask.return_value = mock_task

            result = await service.create_task(
                title="Buy milk",
                description="From the store",
            )

        session.add.assert_called_once()
        session.commit.assert_awaited()
        assert result.title == "Buy milk"

    @pytest.mark.asyncio
    async def test_create_task_fires_created_event(self):
        session = make_mock_session()
        service = TaskService(session)
        session.refresh.side_effect = lambda obj: None

        with patch("app.services.task_service.Task") as MockTask:
            mock_task = make_task()
            MockTask.return_value = mock_task

            with patch.object(service, "create_task_event", new_callable=AsyncMock) as mock_event:
                await service.create_task(title="T", description="D")

            # First call must be CREATED event
            first_call = mock_event.call_args_list[0]
            assert first_call.kwargs["event_type"] == TaskEventTypeEnum.CREATED

    @pytest.mark.asyncio
    async def test_create_task_assigned_sets_in_progress(self):
        """When created with an assigned agent, status should be IN_PROGRESS"""
        session = make_mock_session()
        service = TaskService(session)
        session.refresh.side_effect = lambda obj: None
        agent_id = uuid4()

        with patch("app.services.task_service.Task") as MockTask:
            mock_task = make_task(assigned_agent_id=agent_id)
            MockTask.return_value = mock_task

            with patch.object(service, "create_task_event", new_callable=AsyncMock):
                await service.create_task(
                    title="T", description="D", assigned_agent_id=agent_id
                )

        assert mock_task.status == TaskStatusEnum.IN_PROGRESS


class TestTaskServiceGet:
    @pytest.mark.asyncio
    async def test_get_task_found(self):
        session = make_mock_session()
        service = TaskService(session)
        task = make_task()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        session.execute.return_value = mock_result

        result = await service.get_task(task.id)
        assert result is task

    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        session = make_mock_session()
        service = TaskService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.get_task(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_tasks_list(self):
        session = make_mock_session()
        service = TaskService(session)
        tasks = [make_task(), make_task(), make_task()]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = tasks
        session.execute.return_value = mock_result

        result = await service.get_tasks()
        assert len(result) == 3


class TestTaskStatusTransitions:
    @pytest.mark.asyncio
    async def test_status_backlog_to_in_progress(self):
        session = make_mock_session()
        service = TaskService(session)
        task = make_task(status=TaskStatusEnum.BACKLOG)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        session.execute.return_value = mock_result
        session.refresh.side_effect = lambda obj: None

        with patch.object(service, "create_task_event", new_callable=AsyncMock):
            result = await service.update_task_status(task.id, TaskStatusEnum.IN_PROGRESS)

        assert task.status == TaskStatusEnum.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_status_done_sets_completed_at(self):
        session = make_mock_session()
        service = TaskService(session)
        task = make_task(status=TaskStatusEnum.IN_PROGRESS)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        session.execute.return_value = mock_result
        session.refresh.side_effect = lambda obj: None

        with patch.object(service, "create_task_event", new_callable=AsyncMock):
            await service.update_task_status(task.id, TaskStatusEnum.DONE)

        assert task.completed_at is not None

    @pytest.mark.asyncio
    async def test_status_failed_sets_completed_at(self):
        session = make_mock_session()
        service = TaskService(session)
        task = make_task(status=TaskStatusEnum.IN_PROGRESS)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        session.execute.return_value = mock_result
        session.refresh.side_effect = lambda obj: None

        with patch.object(service, "create_task_event", new_callable=AsyncMock):
            await service.update_task_status(task.id, TaskStatusEnum.FAILED)

        assert task.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_status_nonexistent_task(self):
        session = make_mock_session()
        service = TaskService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.update_task_status(uuid4(), TaskStatusEnum.DONE)
        assert result is None

    @pytest.mark.asyncio
    async def test_status_change_emits_event(self):
        session = make_mock_session()
        service = TaskService(session)
        task = make_task(status=TaskStatusEnum.BACKLOG)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        session.execute.return_value = mock_result
        session.refresh.side_effect = lambda obj: None

        with patch.object(service, "create_task_event", new_callable=AsyncMock) as mock_event:
            await service.update_task_status(task.id, TaskStatusEnum.IN_PROGRESS)

        mock_event.assert_awaited_once()
        assert mock_event.call_args.kwargs["event_type"] == TaskEventTypeEnum.STARTED


class TestTaskAssignment:
    @pytest.mark.asyncio
    async def test_assign_task_sets_agent_and_status(self):
        session = make_mock_session()
        service = TaskService(session)
        task = make_task(status=TaskStatusEnum.BACKLOG)
        agent_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        session.execute.return_value = mock_result
        session.refresh.side_effect = lambda obj: None

        with patch.object(service, "create_task_event", new_callable=AsyncMock):
            result = await service.assign_task(task.id, agent_id)

        assert task.assigned_agent_id == agent_id
        assert task.status == TaskStatusEnum.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_assign_nonexistent_task_returns_none(self):
        session = make_mock_session()
        service = TaskService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.assign_task(uuid4(), uuid4())
        assert result is None
