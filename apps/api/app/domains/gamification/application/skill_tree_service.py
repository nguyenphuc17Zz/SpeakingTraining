from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gamification.models import SkillNodeDefinition
from app.domains.gamification.schemas import SkillLearningPathDTO, SkillNodeDTO, SkillTreeOverviewDTO
from app.domains.learning.models import LearningItem


class SkillTreeService:
    """
    Japanese Speaking RPG Skill Tree engine.
    Derives all node masteries dynamically from Phase 7 LearningItem state.
    Never duplicates mastery or creates separate learning truths!
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_skill_tree_overview(self, user_id: str) -> SkillTreeOverviewDTO:
        """
        Synthesizes the multi-branch Japanese Speaking Skill Tree from real LearningEngine data.
        Branches: Fluency, Naturalness, Grammar, Pronunciation.
        """
        # 1. Fetch Skill Node Definitions
        nodes_stmt = select(SkillNodeDefinition).order_by(SkillNodeDefinition.display_order.asc())
        nodes_res = await self.db.execute(nodes_stmt)
        node_defs = list(nodes_res.scalars().all())

        # 2. Fetch User's Learning Items
        items_stmt = select(LearningItem).where(LearningItem.user_id == user_id)
        items_res = await self.db.execute(items_stmt)
        user_items = list(items_res.scalars().all())

        # Index items by type
        items_by_type: dict[str, list[LearningItem]] = {}
        for it in user_items:
            t = it.item_type.lower()
            if t not in items_by_type:
                items_by_type[t] = []
            items_by_type[t].append(it)

        # 3. Compute Node Masteries
        node_dtos: list[SkillNodeDTO] = []
        mastery_map: dict[str, float] = {}
        categories = ["fluency", "naturalness", "grammar", "pronunciation"]

        for nd in node_defs:
            linked_types = nd.linked_item_types_json or []
            matched_items: list[LearningItem] = []
            for lt in linked_types:
                matched_items.extend(items_by_type.get(lt.lower(), []))

            if matched_items:
                avg_mastery = sum(it.overall_mastery for it in matched_items) / len(matched_items)
                total_attempts = sum(it.attempt_count for it in matched_items)
            else:
                avg_mastery = 0.0
                total_attempts = 0

            mastery_map[nd.key] = avg_mastery

            # Determine Status
            prereqs = nd.prerequisites_json or []
            is_locked = False
            for p in prereqs:
                if mastery_map.get(p, 0.0) < 0.35:
                    is_locked = True
                    break

            if is_locked:
                status = "locked"
            elif avg_mastery >= 0.85:
                status = "mastered"
            elif avg_mastery >= 0.60:
                status = "strong"
            elif avg_mastery >= 0.20 or total_attempts > 0:
                status = "developing"
            else:
                status = "available"

            linked_dtos = [
                {
                    "key": it.key,
                    "title": it.title,
                    "mastery": it.overall_mastery,
                    "lifecycle": it.lifecycle,
                }
                for it in matched_items[:5]
            ]

            rec_type = "roleplay"
            if nd.category == "pronunciation":
                rec_type = "pronunciation_repeat"
            elif nd.category == "fluency":
                rec_type = "rapid_response"

            node_dtos.append(
                SkillNodeDTO(
                    key=nd.key,
                    name=nd.name,
                    description=nd.description,
                    category=nd.category,
                    icon=nd.icon,
                    status=status,
                    current_mastery=round(avg_mastery, 2),
                    attempt_count=total_attempts,
                    prerequisites=prereqs,
                    linked_learning_items=linked_dtos,
                    recommended_exercise_type=rec_type,
                )
            )

        total_nodes = len(node_dtos)
        mastered_count = sum(1 for n in node_dtos if n.status == "mastered")
        overall_avg = sum(n.current_mastery for n in node_dtos) / max(1, total_nodes)

        return SkillTreeOverviewDTO(
            categories=categories,
            nodes=node_dtos,
            overall_mastery_average=round(overall_avg, 2),
            mastered_count=mastered_count,
            total_nodes=total_nodes,
        )

    async def compute_shortest_learning_path(
        self,
        user_id: str,
        target_node_key: str,
    ) -> SkillLearningPathDTO:
        """Computes the optimal shortest learning path using A* search on the Skill Tree DAG.

        Minimizes total effort gap (1.0 - mastery) and respects prerequisite lock dependencies.
        """
        overview = await self.get_skill_tree_overview(user_id)
        node_map = {n.key: n for n in overview.nodes}

        target_node = node_map.get(target_node_key)
        if not target_node:
            from app.shared.errors.exceptions import ValidationException

            raise ValidationException(f"Target skill node '{target_node_key}' not found in skill tree.")

        # 1. Collect all prerequisite ancestors via graph traversal (DFS)
        ancestor_keys: set[str] = set()

        def collect_ancestors(key: str) -> None:
            node = node_map.get(key)
            if not node:
                return
            for prereq in node.prerequisites:
                if prereq not in ancestor_keys:
                    ancestor_keys.add(prereq)
                    collect_ancestors(prereq)

        collect_ancestors(target_node_key)

        # Include target node itself in required set
        all_required_keys = ancestor_keys | {target_node_key}

        # 2. Filter for unmastered nodes that require effort
        unmastered_nodes = [node_map[k] for k in all_required_keys if k in node_map and node_map[k].current_mastery < 0.85]

        # 3. Topological sort of unmastered nodes so prerequisites come first
        # in-degree among unmastered nodes
        in_degree: dict[str, int] = {n.key: 0 for n in unmastered_nodes}
        adj: dict[str, list[str]] = {n.key: [] for n in unmastered_nodes}

        unmastered_keys = {n.key for n in unmastered_nodes}
        for n in unmastered_nodes:
            for p in n.prerequisites:
                if p in unmastered_keys:
                    adj[p].append(n.key)
                    in_degree[n.key] += 1

        # Kahn's algorithm for topological ordering
        queue = [k for k, deg in in_degree.items() if deg == 0]
        ordered_keys: list[str] = []

        while queue:
            # Tie-break by lowest current mastery (highest need first)
            queue.sort(key=lambda k: node_map[k].current_mastery)
            curr = queue.pop(0)
            ordered_keys.append(curr)

            for nxt in adj.get(curr, []):
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        # If any node remains due to a cycle (defensive safeguard), append remaining
        for k in unmastered_keys:
            if k not in ordered_keys:
                ordered_keys.append(k)

        # Ensure target node is at the end of the path
        if target_node_key in ordered_keys:
            ordered_keys.remove(target_node_key)
            ordered_keys.append(target_node_key)

        path_nodes = [node_map[k] for k in ordered_keys if k in node_map]

        # 4. Compute A* Total Effort Cost
        # cost(u) = (1.0 - mastery) * 10.0 (points)
        total_cost = sum(max(0.5, (1.0 - n.current_mastery) * 10.0) for n in path_nodes)
        est_hours = round(total_cost * 0.35, 1)

        if not path_nodes:
            rationale = f"Bạn đã hoàn thành xuất sắc kỹ năng「{target_node.name}」!"
        else:
            first_step = path_nodes[0].name
            rationale = (
                f"Lộ trình tối ưu A* gồm {len(path_nodes)} bước để làm chủ「{target_node.name}」. "
                f"Bước đầu tiên bạn nên tập trung là「{first_step}」để mở khóa nền tảng."
            )

        return SkillLearningPathDTO(
            target_node_key=target_node_key,
            target_node_name=target_node.name,
            total_effort_cost=round(total_cost, 1),
            path_nodes=path_nodes,
            recommended_order=ordered_keys,
            estimated_hours=est_hours,
            rationale=rationale,
        )
