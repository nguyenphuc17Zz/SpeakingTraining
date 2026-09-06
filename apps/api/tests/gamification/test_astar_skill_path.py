import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.gamification.application.skill_tree_service import SkillTreeService
from app.shared.errors.exceptions import ValidationException


@pytest.mark.asyncio
async def test_compute_shortest_learning_path_with_prerequisites(db_session: AsyncSession):
    """Verify A* correctly discovers prerequisite ancestors in topological sequence."""
    skill_service = SkillTreeService(db_session)
    user_id = "test_user_astar_1"

    # fluency_long_response requires fluency_response_speed
    path_dto = await skill_service.compute_shortest_learning_path(
        user_id=user_id,
        target_node_key="fluency_long_response",
    )

    assert path_dto.target_node_key == "fluency_long_response"
    assert path_dto.total_effort_cost > 0
    assert path_dto.estimated_hours > 0
    assert len(path_dto.path_nodes) >= 2

    # Prerequisite must precede the target node in recommended_order
    idx_prereq = path_dto.recommended_order.index("fluency_response_speed")
    idx_target = path_dto.recommended_order.index("fluency_long_response")
    assert idx_prereq < idx_target
    assert path_dto.recommended_order[-1] == "fluency_long_response"
    assert "A*" in path_dto.rationale


@pytest.mark.asyncio
async def test_compute_shortest_learning_path_root_node(db_session: AsyncSession):
    """Verify single root node path calculation without prerequisites."""
    skill_service = SkillTreeService(db_session)
    user_id = "test_user_astar_2"

    path_dto = await skill_service.compute_shortest_learning_path(
        user_id=user_id,
        target_node_key="grammar_particles",
    )

    assert path_dto.target_node_key == "grammar_particles"
    assert path_dto.recommended_order == ["grammar_particles"]
    assert len(path_dto.path_nodes) == 1


@pytest.mark.asyncio
async def test_compute_shortest_learning_path_invalid_key(db_session: AsyncSession):
    """Verify validation exception when target node key is unknown."""
    skill_service = SkillTreeService(db_session)
    user_id = "test_user_astar_3"

    with pytest.raises(ValidationException):
        await skill_service.compute_shortest_learning_path(
            user_id=user_id,
            target_node_key="non_existent_skill_key",
        )
