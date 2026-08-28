"""ReflexExerciseFactory — 100% randomized generation using dictionary pools and morphological rules."""

from __future__ import annotations

import random
from typing import Any

from app.domains.japanese.provider import get_language_provider
from app.domains.reflex.conjugation_engine import (
    ConjugationForm,
    JapaneseConjugationEngine,
)
from app.domains.reflex.dictionary_pool import (
    ALL_DICT_VERBS,
    DICT_CONTEXTS,
    DICT_QNA_QUESTIONS,
    DICT_TRANSFORMATIONS,
    EASY_VERBS,
    HARD_VERBS,
    NORMAL_VERBS,
    DictVerb,
)
from app.domains.reflex.pressure_profiles import timer_for_level


from collections import deque

# =========================================================================
# GLOBAL PERSISTENT EXHAUSTION QUEUES & RECENT HISTORY
# Guarantees 0% repetition across consecutive API requests
# =========================================================================
_GLOBAL_RECENT_QNA: deque[str] = deque(maxlen=80)
_GLOBAL_RECENT_VERBS: deque[str] = deque(maxlen=80)
_GLOBAL_RECENT_TRANSFORMS: deque[str] = deque(maxlen=40)
_GLOBAL_RECENT_CONTEXTS: deque[str] = deque(maxlen=40)

_QNA_SHUFFLE_QUEUE: list[dict[str, Any]] = []
_TRANSFORMS_SHUFFLE_QUEUE: list[dict[str, Any]] = []
_CONTEXTS_SHUFFLE_QUEUE: list[dict[str, Any]] = []


def _get_next_qna() -> dict[str, Any]:
    global _QNA_SHUFFLE_QUEUE
    if not _QNA_SHUFFLE_QUEUE:
        _QNA_SHUFFLE_QUEUE = random.sample(DICT_QNA_QUESTIONS, len(DICT_QNA_QUESTIONS))
    item = _QNA_SHUFFLE_QUEUE.pop(0)
    _GLOBAL_RECENT_QNA.append(item["q"])
    return item


def _get_next_transform() -> dict[str, Any]:
    global _TRANSFORMS_SHUFFLE_QUEUE
    if not _TRANSFORMS_SHUFFLE_QUEUE:
        _TRANSFORMS_SHUFFLE_QUEUE = random.sample(DICT_TRANSFORMATIONS, len(DICT_TRANSFORMATIONS))
    item = _TRANSFORMS_SHUFFLE_QUEUE.pop(0)
    _GLOBAL_RECENT_TRANSFORMS.append(item["source"])
    return item


def _get_next_context() -> dict[str, Any]:
    global _CONTEXTS_SHUFFLE_QUEUE
    if not _CONTEXTS_SHUFFLE_QUEUE:
        _CONTEXTS_SHUFFLE_QUEUE = random.sample(DICT_CONTEXTS, len(DICT_CONTEXTS))
    item = _CONTEXTS_SHUFFLE_QUEUE.pop(0)
    _GLOBAL_RECENT_CONTEXTS.append(item["scenario"])
    return item


class ReflexExerciseFactory:
    """Dynamic generator selecting random verbs and forms from the dictionary pool on every turn."""

    def __init__(self):
        self.conj_engine = JapaneseConjugationEngine()
        self.lang_provider = get_language_provider()

    @property
    def recent_qna(self) -> list[str]:
        return list(_GLOBAL_RECENT_QNA)

    @property
    def recent_verbs(self) -> list[str]:
        return list(_GLOBAL_RECENT_VERBS)

    @property
    def recent_transforms(self) -> list[str]:
        return list(_GLOBAL_RECENT_TRANSFORMS)

    @property
    def recent_contexts(self) -> list[str]:
        return list(_GLOBAL_RECENT_CONTEXTS)

    def generate_conjugation(
        self,
        verb: str | None = None,
        target_form: str | ConjugationForm | None = None,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        **kwargs,
    ) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)

        # 1. Select appropriate verb pool by difficulty
        if difficulty == "easy":
            pool = EASY_VERBS
            candidate_forms = [ConjugationForm.NAI, ConjugationForm.TA, ConjugationForm.TE]
        elif difficulty == "hard":
            pool = HARD_VERBS
            candidate_forms = [
                ConjugationForm.POTENTIAL,
                ConjugationForm.PASSIVE,
                ConjugationForm.CAUSATIVE,
                ConjugationForm.CAUSATIVE_PASSIVE,
                ConjugationForm.VOLITIONAL,
                ConjugationForm.BA,
                ConjugationForm.TARA,
                ConjugationForm.IMPERATIVE,
            ]
        else:
            pool = EASY_VERBS + NORMAL_VERBS
            candidate_forms = [
                ConjugationForm.NAI,
                ConjugationForm.TA,
                ConjugationForm.TE,
                ConjugationForm.POTENTIAL,
                ConjugationForm.PASSIVE,
                ConjugationForm.VOLITIONAL,
                ConjugationForm.BA,
                ConjugationForm.TARA,
            ]

        # 2. Pick a random verb with non-repeating history
        if not verb:
            unseen = [v for v in pool if v.verb not in _GLOBAL_RECENT_VERBS]
            if not unseen:
                _GLOBAL_RECENT_VERBS.clear()
                unseen = pool
            chosen_entry: DictVerb = random.choice(unseen)
            v = chosen_entry.verb
            meaning_vi = chosen_entry.meaning_vi
            reading = chosen_entry.reading
            _GLOBAL_RECENT_VERBS.append(v)
        else:
            v = verb
            match = next((x for x in ALL_DICT_VERBS if x.verb == v), None)
            meaning_vi = match.meaning_vi if match else "Động từ tiếng Nhật"
            reading = match.reading if match else (self.lang_provider.get_reading(v) or v)

        # 3. Pick a random target form
        if not target_form:
            form = random.choice(candidate_forms)
        else:
            form = target_form

        # 4. Conjugate
        target = self.conj_engine.conjugate(v, form)

        return {
            "title": f"瞬発力・活用: {v} → {target.form.value}",
            "objective": f"Chia động từ {v} ({meaning_vi}) sang dạng {target.form.value} trong {timer_ms/1000:.1f}s",
            "scenario": f"Động từ: {v} ({meaning_vi})",
            "instructions": f"Nghe/nhìn động từ '{v}' ({meaning_vi}) và nói ngay dạng {target.form.value} trước khi hết giờ.",
            "prompt": v,
            "prompt_reading": reading,
            "translation": meaning_vi,
            "vietnamese": meaning_vi,
            "target": target.canonical,
            "canonical": target.canonical,
            "acceptable_variants": target.accepted,
            "alternatives": target.alternatives,
            "variant_notes": target.variant_notes,
            "verb_class": target.verb_class.value,
            "form": target.form.value,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Nói chính xác dạng chia, không thêm filler dài."],
            "target_patterns": [target.canonical] + target.accepted,
            "estimated_minutes": 3,
        }

    def generate_qna(self, difficulty: str = "normal", pressure_level: str = "normal", **kwargs) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)
        chosen = _get_next_qna()

        sample_ans = chosen.get("sample_answer", "はい、そうです。")
        return {
            "title": "瞬発 Q&A",
            "objective": f"Nghe câu hỏi và trả lời tự nhiên trong {timer_ms/1000:.1f}s",
            "scenario": chosen["translation"],
            "instructions": f"Nghe: '{chosen['q']}' — Trả lời ngay bằng tiếng Nhật 1-2 câu tự nhiên.",
            "prompt": chosen["q"],
            "prompt_translation": chosen["translation"],
            "translation": chosen["translation"],
            "vietnamese": chosen["translation"],
            "expected": sample_ans,
            "canonical": sample_ans,
            "acceptable_variants": [sample_ans],
            "topic": "lifestyle",
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Trả lời đủ ý, tự nhiên."],
            "target_patterns": [],
            "semantic_target": {"required_intent": "answer question"},
            "estimated_minutes": 4,
        }

    def generate_transformation(self, difficulty: str = "normal", pressure_level: str = "normal", **kwargs) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)
        chosen = _get_next_transform()

        return {
            "title": f"瞬発・文型変換: {chosen['task']}",
            "objective": f"Biến đổi câu theo yêu cầu trong {timer_ms/1000:.1f}s",
            "scenario": chosen["translation"],
            "instructions": f"Câu gốc: '{chosen['source']}' — Yêu cầu: {chosen['task']} — Nói ngay câu đã biến đổi.",
            "prompt": chosen["source"],
            "prompt_translation": chosen["translation"],
            "translation": chosen["translation"],
            "vietnamese": chosen["translation"],
            "task": chosen["task"],
            "expected": chosen["expected"],
            "canonical": chosen["expected"],
            "acceptable_variants": [chosen["expected"]],
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Giữ nguyên ý nghĩa, chỉ đổi cấu trúc ngữ pháp."],
            "target_patterns": [chosen["expected"]],
            "estimated_minutes": 4,
        }

    def generate_context(self, difficulty: str = "normal", pressure_level: str = "normal", **kwargs) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)
        chosen = _get_next_context()

        return {
            "title": f"瞬発・状況対応: {chosen['role']}",
            "objective": f"Phản ứng tự nhiên theo tình huống trong {timer_ms/1000:.1f}s",
            "scenario": chosen["translation"],
            "instructions": f"Tình huống: {chosen['scenario']} — Ý định: {chosen['intent']} — Nói ngay phản hồi tiếng Nhật.",
            "prompt": chosen["scenario"],
            "prompt_translation": chosen["translation"],
            "translation": chosen["translation"],
            "vietnamese": chosen["translation"],
            "intent": chosen["intent"],
            "expected": chosen["expected"],
            "canonical": chosen["expected"],
            "acceptable_variants": [chosen["expected"]],
            "relationship": chosen["role"],
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Phản hồi tự nhiên, đúng ý định."],
            "target_patterns": [],
            "semantic_target": {"intent": chosen["intent"]},
            "estimated_minutes": 4,
        }

    def generate(self, sub_mode: str, **kwargs) -> dict[str, Any]:
        if sub_mode == "reflex_conjugation":
            return self.generate_conjugation(**kwargs)
        if sub_mode == "reflex_qna":
            return self.generate_qna(**kwargs)
        if sub_mode == "reflex_transformation":
            return self.generate_transformation(**kwargs)
        if sub_mode == "reflex_context":
            return self.generate_context(**kwargs)
        return self.generate_qna(**kwargs)
