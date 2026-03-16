"""
Unit tests for AgentService — CRUD and status transitions
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.agent import Agent, AgentTool
from app.models.enums import AgentStatusEnum, DomainEnum
from app.services.agent_service import AgentService


def make_mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def make_agent(**kwargs) -> Agent:
    defaults = dict(
        id=uuid4(),
        name="TestBot",
        gender="MALE",
        class_id=uuid4(),
        domain=DomainEnum.TECH.value,
        role_description="A test agent",
        personality={},
        llm_config_id=uuid4(),
        avatar_config={},
        status=AgentStatusEnum.IDLE,
        is_orchestrator=False,
    )
    defaults.update(kwargs)
    agent = MagicMock(spec=Agent)
    for k, v in defaults.items():
        setattr(agent, k, v)
    return agent


class TestAgentServiceCreate:
    @pytest.mark.asyncio
    async def test_create_agent_returns_agent(self):
        session = make_mock_session()
        # refresh sets the agent on session
        service = AgentService(session)

        class_id = uuid4()
        llm_id = uuid4()

        # Patch Agent constructor and session.refresh to simulate DB behavior
        with patch("app.services.agent_service.Agent") as MockAgent:
            mock_agent = make_agent(name="Alpha")
            MockAgent.return_value = mock_agent
            session.refresh.side_effect = lambda obj: None

            result = await service.create_agent(
                name="Alpha",
                gender="MALE",
                class_id=class_id,
                domain=DomainEnum.TECH.value,
                role_description="Alpha agent",
                personality={},
                llm_config_id=llm_id,
                avatar_config={},
            )

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()
        assert result.name == "Alpha"

    @pytest.mark.asyncio
    async def test_create_orchestrator_agent(self):
        session = make_mock_session()
        service = AgentService(session)

        with patch("app.services.agent_service.Agent") as MockAgent:
            mock_agent = make_agent(name="Orch", is_orchestrator=True)
            MockAgent.return_value = mock_agent
            session.refresh.side_effect = lambda obj: None

            result = await service.create_agent(
                name="Orch",
                gender="MALE",
                class_id=uuid4(),
                domain=DomainEnum.TECH.value,
                role_description="Orchestrator",
                personality={},
                llm_config_id=uuid4(),
                avatar_config={},
                is_orchestrator=True,
            )

        kwargs_passed = MockAgent.call_args.kwargs
        assert kwargs_passed["is_orchestrator"] is True


class TestAgentServiceGet:
    @pytest.mark.asyncio
    async def test_get_agent_found(self):
        session = make_mock_session()
        service = AgentService(session)
        expected = make_agent()
        agent_id = expected.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected
        session.execute.return_value = mock_result

        result = await service.get_agent(agent_id)
        assert result is expected

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self):
        session = make_mock_session()
        service = AgentService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.get_agent(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_agents_returns_list(self):
        session = make_mock_session()
        service = AgentService(session)
        agents = [make_agent(), make_agent()]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = agents
        session.execute.return_value = mock_result

        result = await service.get_agents()
        assert len(result) == 2


class TestAgentServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_agent_name(self):
        session = make_mock_session()
        service = AgentService(session)
        agent = make_agent(name="OldName")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = agent
        session.execute.return_value = mock_result
        session.refresh.side_effect = lambda obj: None

        result = await service.update_agent(agent.id, name="NewName")

        assert agent.name == "NewName"
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_nonexistent_agent_returns_none(self):
        session = make_mock_session()
        service = AgentService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.update_agent(uuid4(), name="X")
        assert result is None


class TestAgentStatusTransitions:
    @pytest.mark.asyncio
    async def test_update_status_idle_to_working(self):
        session = make_mock_session()
        service = AgentService(session)
        task_id = uuid4()
        agent = make_agent(status=AgentStatusEnum.IDLE)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = agent
        session.execute.return_value = mock_result
        session.refresh.side_effect = lambda obj: None

        result = await service.update_agent_status(
            agent.id, AgentStatusEnum.WORKING, current_task_id=task_id
        )

        assert agent.status == AgentStatusEnum.WORKING
        assert agent.current_task_id == task_id

    @pytest.mark.asyncio
    async def test_delete_agent_sets_offline(self):
        session = make_mock_session()
        service = AgentService(session)
        agent = make_agent(status=AgentStatusEnum.IDLE)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = agent
        session.execute.return_value = mock_result

        success = await service.delete_agent(agent.id)

        assert success is True
        assert agent.status == AgentStatusEnum.OFFLINE

    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent_returns_false(self):
        session = make_mock_session()
        service = AgentService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.delete_agent(uuid4())
        assert result is False


class TestAgentToolAssignment:
    @pytest.mark.asyncio
    async def test_assign_tool(self):
        session = make_mock_session()
        service = AgentService(session)
        agent_id = uuid4()
        tool_id = uuid4()

        with patch("app.services.agent_service.AgentTool") as MockAgentTool:
            mock_at = MagicMock(spec=AgentTool)
            MockAgentTool.return_value = mock_at

            result = await service.assign_tool(agent_id, tool_id)

        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unassign_tool_success(self):
        session = make_mock_session()
        service = AgentService(session)
        agent_id = uuid4()
        tool_id = uuid4()

        mock_at = MagicMock(spec=AgentTool)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_at
        session.execute.return_value = mock_result

        result = await service.unassign_tool(agent_id, tool_id)

        assert result is True
        session.delete.assert_awaited_once_with(mock_at)
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unassign_tool_not_found(self):
        session = make_mock_session()
        service = AgentService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.unassign_tool(uuid4(), uuid4())
        assert result is False
