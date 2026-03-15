"""
Skills API Endpoints

CRUD operations for skills and skill assignments.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database import get_session
from app.models.skill import (
    Skill, SkillParameter, AgentSkill, SkillExecutionLog,
    SkillCreateSchema, SkillUpdateSchema, SkillResponseSchema,
    SkillParameterSchema, AgentSkillAssignSchema, AgentSkillResponseSchema,
    SkillExecuteSchema, SkillExecutionResponseSchema,
    SkillLanguage
)
from app.models.agent import Agent
from app.services.skill_execution_service import SkillExecutionService, get_skill_execution_service
from app.core.auth import get_current_user
from app.utils.id_generator import generate_id
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=List[SkillResponseSchema])
async def list_skills(
    public_only: bool = False,
    official_only: bool = False,
    search: Optional[str] = None,
    language: Optional[SkillLanguage] = None,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    List available skills.
    
    Returns public skills and user's own skills.
    """
    query = db.query(Skill)
    
    # Filter by visibility
    if public_only:
        query = query.filter(Skill.is_public == True)
    else:
        # Show public skills + user's own skills
        query = query.filter(
            or_(
                Skill.is_public == True,
                Skill.created_by == current_user.id if hasattr(current_user, 'id') else True
            )
        )
    
    if official_only:
        query = query.filter(Skill.is_official == True)
    
    if language:
        query = query.filter(Skill.language == language)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Skill.name.ilike(search_filter),
                Skill.description.ilike(search_filter)
            )
        )
    
    skills = query.order_by(Skill.usage_count.desc()).all()
    return skills


@router.post("", response_model=SkillResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreateSchema,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Create a new skill."""
    
    # Validate code before creating
    execution_service = SkillExecutionService(db)
    try:
        execution_service.validate_code(skill_data.code, skill_data.language)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code validation failed: {str(e)}"
        )
    
    # Create skill
    skill = Skill(
        id=generate_id(),
        name=skill_data.name,
        description=skill_data.description,
        code=skill_data.code,
        language=skill_data.language,
        created_by=current_user.id if hasattr(current_user, 'id') else None,
        is_public=skill_data.is_public,
        version="1.0.0"
    )
    
    db.add(skill)
    db.flush()  # Get skill.id
    
    # Create parameters
    for param_data in skill_data.parameters:
        param = SkillParameter(
            id=generate_id(),
            skill_id=skill.id,
            name=param_data.name,
            param_type=param_data.param_type,
            description=param_data.description,
            required=param_data.required,
            default_value=param_data.default_value
        )
        db.add(param)
    
    db.commit()
    db.refresh(skill)
    
    logger.info(f"Created skill: {skill.name} (id: {skill.id})")
    return skill


@router.get("/{skill_id}", response_model=SkillResponseSchema)
async def get_skill(
    skill_id: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Get skill details."""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Hide code if not owner and not public
    if not skill.is_public:
        if not hasattr(current_user, 'id') or skill.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this skill"
            )
    
    return skill


@router.put("/{skill_id}", response_model=SkillResponseSchema)
async def update_skill(
    skill_id: str,
    skill_data: SkillUpdateSchema,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Update a skill."""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Check ownership
    if skill.created_by != current_user.id if hasattr(current_user, 'id') else True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own skills"
        )
    
    # Validate new code if provided
    if skill_data.code:
        execution_service = SkillExecutionService(db)
        try:
            execution_service.validate_code(skill_data.code, skill.language)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Code validation failed: {str(e)}"
            )
        skill.code = skill_data.code
    
    # Update fields
    if skill_data.name:
        skill.name = skill_data.name
    if skill_data.description is not None:
        skill.description = skill_data.description
    if skill_data.is_public is not None:
        skill.is_public = skill_data.is_public
    
    # Update parameters if provided
    if skill_data.parameters is not None:
        # Remove old parameters
        db.query(SkillParameter).filter(SkillParameter.skill_id == skill_id).delete()
        
        # Add new parameters
        for param_data in skill_data.parameters:
            param = SkillParameter(
                id=generate_id(),
                skill_id=skill.id,
                name=param_data.name,
                param_type=param_data.param_type,
                description=param_data.description,
                required=param_data.required,
                default_value=param_data.default_value
            )
            db.add(param)
    
    # Increment version
    version_parts = skill.version.split('.')
    version_parts[-1] = str(int(version_parts[-1]) + 1)
    skill.version = '.'.join(version_parts)
    
    db.commit()
    db.refresh(skill)
    
    logger.info(f"Updated skill: {skill.name} (id: {skill.id})")
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Delete a skill."""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Check ownership or admin
    if skill.created_by != current_user.id if hasattr(current_user, 'id') else True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own skills"
        )
    
    db.delete(skill)
    db.commit()
    
    logger.info(f"Deleted skill: {skill_id}")


@router.post("/{skill_id}/execute", response_model=SkillExecutionResponseSchema)
async def execute_skill(
    skill_id: str,
    execute_data: SkillExecuteSchema,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Execute a skill with given parameters.
    
    This is primarily for testing skills during development.
    """
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Check permission
    if not skill.is_public:
        if not hasattr(current_user, 'id') or skill.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to execute this skill"
            )
    
    # Execute
    execution_service = SkillExecutionService(db)
    result = await execution_service.execute_skill(
        skill=skill,
        parameters=execute_data.parameters,
        agent_id=current_user.id if hasattr(current_user, 'id') else None,
        timeout=execute_data.timeout
    )
    
    return result


# Agent-Skill Assignment Endpoints

@router.get("/agent/{agent_id}/skills", response_model=List[AgentSkillResponseSchema])
async def list_agent_skills(
    agent_id: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """List skills assigned to an agent."""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    agent_skills = db.query(AgentSkill).filter(
        AgentSkill.agent_id == agent_id
    ).all()
    
    # Enrich with skill names
    result = []
    for ag in agent_skills:
        skill = db.query(Skill).filter(Skill.id == ag.skill_id).first()
        if skill:
            result.append({
                "id": ag.id,
                "agent_id": ag.agent_id,
                "skill_id": ag.skill_id,
                "skill_name": skill.name,
                "skill_description": skill.description,
                "is_enabled": ag.is_enabled,
                "permission_level": ag.permission_level,
                "use_count": ag.use_count,
                "last_used_at": ag.last_used_at,
                "config": ag.config
            })
    
    return result


@router.post("/agent/{agent_id}/skills", response_model=AgentSkillResponseSchema)
async def assign_skill_to_agent(
    agent_id: str,
    assign_data: AgentSkillAssignSchema,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Assign a skill to an agent."""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify skill exists
    skill = db.query(Skill).filter(Skill.id == assign_data.skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Check if already assigned
    existing = db.query(AgentSkill).filter(
        and_(
            AgentSkill.agent_id == agent_id,
            AgentSkill.skill_id == assign_data.skill_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill already assigned to this agent"
        )
    
    # Create assignment
    agent_skill = AgentSkill(
        id=generate_id(),
        agent_id=agent_id,
        skill_id=assign_data.skill_id,
        config=assign_data.config,
        permission_level=assign_data.permission_level,
        is_enabled=True
    )
    
    db.add(agent_skill)
    db.commit()
    db.refresh(agent_skill)
    
    logger.info(f"Assigned skill {skill.name} to agent {agent_id}")
    
    return {
        "id": agent_skill.id,
        "agent_id": agent_skill.agent_id,
        "skill_id": agent_skill.skill_id,
        "skill_name": skill.name,
        "skill_description": skill.description,
        "is_enabled": agent_skill.is_enabled,
        "permission_level": agent_skill.permission_level,
        "use_count": agent_skill.use_count,
        "last_used_at": agent_skill.last_used_at,
        "config": agent_skill.config
    }


@router.put("/agent/{agent_id}/skills/{agent_skill_id}", response_model=AgentSkillResponseSchema)
async def update_agent_skill(
    agent_id: str,
    agent_skill_id: str,
    updates: AgentSkillAssignSchema,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Update an agent's skill assignment."""
    agent_skill = db.query(AgentSkill).filter(
        and_(
            AgentSkill.id == agent_skill_id,
            AgentSkill.agent_id == agent_id
        )
    ).first()
    
    if not agent_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill assignment not found"
        )
    
    agent_skill.config = updates.config
    agent_skill.permission_level = updates.permission_level
    
    db.commit()
    db.refresh(agent_skill)
    
    skill = db.query(Skill).filter(Skill.id == agent_skill.skill_id).first()
    
    return {
        "id": agent_skill.id,
        "agent_id": agent_skill.agent_id,
        "skill_id": agent_skill.skill_id,
        "skill_name": skill.name if skill else "Unknown",
        "skill_description": skill.description if skill else None,
        "is_enabled": agent_skill.is_enabled,
        "permission_level": agent_skill.permission_level,
        "use_count": agent_skill.use_count,
        "last_used_at": agent_skill.last_used_at,
        "config": agent_skill.config
    }


@router.delete("/agent/{agent_id}/skills/{agent_skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_skill_from_agent(
    agent_id: str,
    agent_skill_id: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Remove a skill from an agent."""
    agent_skill = db.query(AgentSkill).filter(
        and_(
            AgentSkill.id == agent_skill_id,
            AgentSkill.agent_id == agent_id
        )
    ).first()
    
    if not agent_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill assignment not found"
        )
    
    db.delete(agent_skill)
    db.commit()
    
    logger.info(f"Removed skill {agent_skill_id} from agent {agent_id}")


@router.get("/agent/{agent_id}/skills/{skill_id}/execute", response_model=SkillExecutionResponseSchema)
async def execute_agent_skill(
    agent_id: str,
    skill_id: str,
    execute_data: SkillExecuteSchema,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Execute a skill on behalf of an agent.
    
    This is the main endpoint used during task execution.
    """
    # Verify agent-skill relationship
    agent_skill = db.query(AgentSkill).filter(
        and_(
            AgentSkill.agent_id == agent_id,
            AgentSkill.skill_id == skill_id
        )
    ).first()
    
    if not agent_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not assigned to this agent"
        )
    
    if not agent_skill.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill is disabled for this agent"
        )
    
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    
    # Merge agent config with execution params
    merged_params = {**agent_skill.config, **execute_data.parameters}
    
    # Execute
    execution_service = SkillExecutionService(db)
    result = await execution_service.execute_skill(
        skill=skill,
        parameters=merged_params,
        agent_id=agent_id,
        timeout=execute_data.timeout
    )
    
    # Update usage stats
    if result["success"]:
        agent_skill.use_count += 1
        agent_skill.last_used_at = datetime.utcnow()
        skill.usage_count += 1
        db.commit()
    
    return result
