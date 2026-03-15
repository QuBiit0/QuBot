"""
Service Tests - Unit tests for business logic

Run with: pytest tests/test_services.py -v
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.assignment_service import AssignmentService, AssignmentScore
from app.models.enums import DomainEnum, AgentStatusEnum, TaskStatusEnum, PriorityEnum


class TestAssignmentService:
    """Test assignment service"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = MagicMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def service(self, mock_session):
        """Create assignment service with mock session"""
        return AssignmentService(mock_session)
    
    def test_score_calculation(self, service):
        """Test assignment score calculation structure"""
        # Create mock agent and task
        agent = MagicMock()
        agent.id = uuid4()
        agent.name = "Test Agent"
        agent.domain = DomainEnum.SOFTWARE.value
        agent.status = AgentStatusEnum.IDLE
        
        task = MagicMock()
        task.id = uuid4()
        task.domain_hint = DomainEnum.SOFTWARE
        
        # Calculate domain match
        score = service._calculate_domain_match(agent, task)
        assert score == 40.0  # Perfect match
        
        # Test different domain
        agent.domain = DomainEnum.FINANCE.value
        task.domain_hint = DomainEnum.SOFTWARE
        score = service._calculate_domain_match(agent, task)
        assert score < 40.0  # Should be lower
    
    def test_availability_score_idle(self, service):
        """Test availability score for idle agent"""
        agent = MagicMock()
        agent.status = AgentStatusEnum.IDLE
        
        score = service._calculate_availability_score(agent)
        assert score == 10.0  # Full score for idle
    
    def test_availability_score_busy(self, service):
        """Test availability score for busy agent"""
        agent = MagicMock()
        agent.status = AgentStatusEnum.WORKING
        
        score = service._calculate_availability_score(agent)
        assert score == 2.0  # Low score for busy


class TestAssignmentScore:
    """Test AssignmentScore dataclass"""
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        score = AssignmentScore(
            agent_id=uuid4(),
            agent_name="Test Agent",
            total_score=85.5,
            domain_match=40.0,
            workload_score=20.0,
            performance_score=20.0,
            availability_score=5.5,
        )
        
        data = score.to_dict()
        
        assert data["agent_id"] == str(score.agent_id)
        assert data["agent_name"] == "Test Agent"
        assert data["total_score"] == 85.5
        assert "breakdown" in data
        assert data["breakdown"]["domain_match"] == 40.0


class TestToolExecution:
    """Test tool execution logic"""
    
    def test_tool_result_creation(self):
        """Test ToolResult creation"""
        from app.core.tools.base import ToolResult
        
        result = ToolResult(
            success=True,
            data={"key": "value"},
            stdout="output",
            execution_time_ms=100,
        )
        
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.execution_time_ms == 100
    
    def test_tool_result_to_dict(self):
        """Test ToolResult to_dict conversion"""
        from app.core.tools.base import ToolResult
        
        result = ToolResult(
            success=True,
            data={"key": "value"},
            execution_time_ms=100,
        )
        
        data = result.to_dict()
        assert data["success"] is True
        assert data["data"] == {"key": "value"}
        assert data["execution_time_ms"] == 100


class TestRealtimeEvent:
    """Test realtime event system"""
    
    def test_event_creation(self):
        """Test realtime event creation"""
        from app.core.realtime import RealtimeEvent, EventType
        
        event = RealtimeEvent.create(
            event_type=EventType.TASK_COMPLETED,
            payload={"task_id": str(uuid4())},
        )
        
        assert event.type == EventType.TASK_COMPLETED
        assert "task_id" in event.payload
        assert event.timestamp is not None
    
    def test_event_to_dict(self):
        """Test event serialization"""
        from app.core.realtime import RealtimeEvent, EventType
        
        event = RealtimeEvent.create(
            event_type=EventType.AGENT_STATUS_CHANGED,
            payload={"agent_id": str(uuid4()), "status": "working"},
            sender_id="test-sender",
        )
        
        data = event.to_dict()
        assert data["type"] == "agent.status_changed"
        assert "payload" in data
        assert data["sender_id"] == "test-sender"
    
    def test_event_to_json(self):
        """Test event JSON serialization"""
        from app.core.realtime import RealtimeEvent, EventType
        
        event = RealtimeEvent.create(
            event_type=EventType.SYSTEM_NOTIFICATION,
            payload={"message": "Test"},
        )
        
        json_str = event.to_json()
        assert "system.notification" in json_str
        assert "Test" in json_str


# Run tests if called directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
