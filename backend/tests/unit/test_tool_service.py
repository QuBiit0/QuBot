"""
Unit tests for ToolService — CRUD and count
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.enums import ToolTypeEnum
from app.models.tool import Tool
from app.services.tool_service import ToolService


def make_mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def make_tool(**kwargs) -> Tool:
    defaults = dict(
        id=uuid4(),
        name="TestTool",
        type=ToolTypeEnum.HTTP_API,
        description="A test tool",
        input_schema={},
        output_schema={},
        config={},
        is_dangerous=False,
    )
    defaults.update(kwargs)
    tool = MagicMock(spec=Tool)
    for k, v in defaults.items():
        setattr(tool, k, v)
    return tool


class TestToolServiceCreate:
    @pytest.mark.asyncio
    async def test_create_tool_returns_tool(self):
        session = make_mock_session()
        service = ToolService(session)

        with patch("app.services.tool_service.Tool") as MockTool:
            mock_tool = make_tool(name="WebFetcher")
            MockTool.return_value = mock_tool
            session.refresh.side_effect = lambda obj: None

            result = await service.create_tool(
                name="WebFetcher",
                tool_type=ToolTypeEnum.WEB_BROWSER,
                description="Browse the web",
                input_schema={"url": "string"},
                output_schema={"content": "string"},
                config={"timeout": 30},
            )

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()
        assert result.name == "WebFetcher"

    @pytest.mark.asyncio
    async def test_create_dangerous_tool(self):
        session = make_mock_session()
        service = ToolService(session)

        with patch("app.services.tool_service.Tool") as MockTool:
            mock_tool = make_tool(name="Shell", is_dangerous=True)
            MockTool.return_value = mock_tool
            session.refresh.side_effect = lambda obj: None

            await service.create_tool(
                name="Shell",
                tool_type=ToolTypeEnum.SYSTEM_SHELL,
                description="Run shell",
                input_schema={},
                output_schema={},
                config={},
                is_dangerous=True,
            )

        kwargs = MockTool.call_args.kwargs
        assert kwargs["is_dangerous"] is True


class TestToolServiceGet:
    @pytest.mark.asyncio
    async def test_get_tool_found(self):
        session = make_mock_session()
        service = ToolService(session)
        expected = make_tool()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected
        session.execute.return_value = mock_result

        result = await service.get_tool(expected.id)
        assert result is expected

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self):
        session = make_mock_session()
        service = ToolService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.get_tool(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_tools_returns_list(self):
        session = make_mock_session()
        service = ToolService(session)
        tools = [make_tool(), make_tool(), make_tool()]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = tools
        session.execute.return_value = mock_result

        result = await service.get_tools()
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_count_tools_returns_integer(self):
        session = make_mock_session()
        service = ToolService(session)

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 7
        session.execute.return_value = mock_result

        count = await service.count_tools()
        assert count == 7

    @pytest.mark.asyncio
    async def test_count_tools_with_type_filter(self):
        session = make_mock_session()
        service = ToolService(session)

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 2
        session.execute.return_value = mock_result

        count = await service.count_tools(tool_type=ToolTypeEnum.WEB_BROWSER)
        assert count == 2
        # Verify execute was called (query was built and executed)
        session.execute.assert_awaited_once()


class TestToolServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_tool_name(self):
        session = make_mock_session()
        service = ToolService(session)
        tool = make_tool(name="OldName")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tool
        session.execute.return_value = mock_result
        session.refresh.side_effect = lambda obj: None

        result = await service.update_tool(tool.id, name="NewName")

        assert tool.name == "NewName"
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_nonexistent_tool_returns_none(self):
        session = make_mock_session()
        service = ToolService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.update_tool(uuid4(), name="X")
        assert result is None


class TestToolServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_tool_success(self):
        session = make_mock_session()
        service = ToolService(session)
        tool = make_tool()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tool
        session.execute.return_value = mock_result

        result = await service.delete_tool(tool.id)

        assert result is True
        session.delete.assert_awaited_once_with(tool)
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_tool_returns_false(self):
        session = make_mock_session()
        service = ToolService(session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await service.delete_tool(uuid4())
        assert result is False
