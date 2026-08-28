from typing import Any


class ExerciseValidator:
    """Quality and pedagogical safety validator for AI-generated and template exercises."""

    @classmethod
    def validate_exercise_data(cls, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validates structure, pedagogical soundness, and safety of exercise definition.
        Returns (is_valid, list_of_issues).
        """
        issues: list[str] = []

        # 1. Required fields
        title = str(data.get("title", "")).strip()
        if len(title) < 3:
            issues.append("Exercise title is too short or missing.")

        objective = str(data.get("objective", "")).strip()
        if len(objective) < 5:
            issues.append("Exercise objective is too short or missing.")

        instructions = str(data.get("instructions", "")).strip()
        if len(instructions) < 10:
            issues.append("Instructions must be at least 10 characters.")

        # 2. Target patterns
        target_patterns = data.get("target_patterns", [])
        if not target_patterns or not isinstance(target_patterns, list):
            issues.append("target_patterns must be a non-empty list of strings.")

        # 3. Estimated minutes boundary
        est_min = data.get("estimated_minutes", 5)
        if not isinstance(est_min, (int, float)) or est_min < 1 or est_min > 45:
            issues.append(f"estimated_minutes ({est_min}) must be between 1 and 45.")

        # 4. Check for leaked complete answers in prompt/instructions
        if target_patterns and isinstance(target_patterns, list):
            for pat in target_patterns:
                pat_str = str(pat).strip()
                # If target pattern is a full sentence (> 25 chars) and literally in instructions
                if len(pat_str) > 25 and pat_str in instructions:
                    issues.append("Instructions appear to leak the exact complete answer sentence.")

        # 5. Quality of Japanese content
        scenario = data.get("scenario")
        if scenario and len(str(scenario)) > 1000:
            issues.append("Scenario description is excessively long.")

        return len(issues) == 0, issues
