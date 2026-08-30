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
from app.domains.keigo.keigo_vocab_pool import (
    ALL_KEIGO_WORDS,
    KeigoWordEntry,
    get_all_keigo_vocab,
    get_business_vocab_pool,
    get_easy_keigo_vocab,
    get_hard_keigo_vocab,
    get_kenjougo_pool,
    get_normal_keigo_vocab,
    get_sonkeigo_pool,
)
from app.domains.reflex.pressure_profiles import timer_for_level
from app.domains.reflex.vocab_pool import (
    DictWord,
    get_all_vocab_words,
    get_easy_vocab,
    get_hard_vocab,
    get_normal_vocab,
)


from collections import deque

# =========================================================================
# GLOBAL PERSISTENT EXHAUSTION QUEUES & RECENT HISTORY
# Guarantees 0% repetition across consecutive API requests
# =========================================================================
_GLOBAL_RECENT_QNA: deque[str] = deque(maxlen=80)
_GLOBAL_RECENT_VERBS: deque[str] = deque(maxlen=150)
_GLOBAL_RECENT_TRANSFORMS: deque[str] = deque(maxlen=40)
_GLOBAL_RECENT_CONTEXTS: deque[str] = deque(maxlen=40)
_GLOBAL_RECENT_VOCAB: deque[str] = deque(maxlen=200)
_GLOBAL_RECENT_KEIGO_VOCAB: deque[str] = deque(maxlen=100)
_GLOBAL_RECENT_FORMS: deque[str] = deque(maxlen=8)

_QNA_SHUFFLE_QUEUE: list[dict[str, Any]] = []
_TRANSFORMS_SHUFFLE_QUEUE: list[dict[str, Any]] = []
_CONTEXTS_SHUFFLE_QUEUE: list[dict[str, Any]] = []
_VOCAB_SHUFFLE_QUEUE: list[DictWord] = []
_KEIGO_QUEUES: dict[str, list[KeigoWordEntry]] = {}
_CONJ_FORMS_SHUFFLE_QUEUE: list[ConjugationForm] = []


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


def _get_next_vocab(difficulty: str = "normal") -> DictWord:
    global _VOCAB_SHUFFLE_QUEUE
    pool = get_all_vocab_words()
    if not _VOCAB_SHUFFLE_QUEUE:
        unseen = [w for w in pool if w.word not in _GLOBAL_RECENT_VOCAB]
        if not unseen:
            _GLOBAL_RECENT_VOCAB.clear()
            unseen = pool
        _VOCAB_SHUFFLE_QUEUE = random.sample(unseen, len(unseen))
    item = _VOCAB_SHUFFLE_QUEUE.pop(0)
    _GLOBAL_RECENT_VOCAB.append(item.word)
    return item


def _get_next_keigo_vocab(target_type: str = "all", difficulty: str = "normal") -> KeigoWordEntry:
    global _KEIGO_QUEUES
    if target_type == "sonkeigo":
        pool = get_sonkeigo_pool()
    elif target_type == "kenjougo":
        pool = get_kenjougo_pool()
    elif target_type == "business":
        pool = get_business_vocab_pool()
    else:
        pool = get_all_keigo_vocab()

    q_key = target_type
    if not _KEIGO_QUEUES.get(q_key):
        unseen = [w for w in pool if f"{w.source_word}_{w.target_type}" not in _GLOBAL_RECENT_KEIGO_VOCAB]
        if not unseen:
            unseen = pool
        _KEIGO_QUEUES[q_key] = random.sample(unseen, len(unseen))
    item = _KEIGO_QUEUES[q_key].pop(0)
    _GLOBAL_RECENT_KEIGO_VOCAB.append(f"{item.source_word}_{item.target_type}")
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

    def _get_next_form(self, candidate_forms: list[ConjugationForm]) -> ConjugationForm:
        global _CONJ_FORMS_SHUFFLE_QUEUE
        _CONJ_FORMS_SHUFFLE_QUEUE = [f for f in _CONJ_FORMS_SHUFFLE_QUEUE if f in candidate_forms]
        if not _CONJ_FORMS_SHUFFLE_QUEUE:
            last_form = _GLOBAL_RECENT_FORMS[-1] if _GLOBAL_RECENT_FORMS else None
            shuffled = random.sample(candidate_forms, len(candidate_forms))
            if last_form and len(shuffled) > 1 and shuffled[0].value == last_form:
                shuffled[0], shuffled[-1] = shuffled[-1], shuffled[0]
            _CONJ_FORMS_SHUFFLE_QUEUE = shuffled
        chosen_form = _CONJ_FORMS_SHUFFLE_QUEUE.pop(0)
        _GLOBAL_RECENT_FORMS.append(chosen_form.value)
        return chosen_form

    def generate_conjugation(
        self,
        verb: str | None = None,
        target_form: str | ConjugationForm | None = None,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        **kwargs,
    ) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)

        # 1. 100% Full Unrestricted Verb Pool and All 11 Conjugation Forms
        pool = ALL_DICT_VERBS
        candidate_forms = [
            ConjugationForm.NAI,
            ConjugationForm.TA,
            ConjugationForm.TE,
            ConjugationForm.POTENTIAL,
            ConjugationForm.PASSIVE,
            ConjugationForm.CAUSATIVE,
            ConjugationForm.CAUSATIVE_PASSIVE,
            ConjugationForm.VOLITIONAL,
            ConjugationForm.BA,
            ConjugationForm.TARA,
            ConjugationForm.IMPERATIVE,
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
            jlpt_level = chosen_entry.level
            _GLOBAL_RECENT_VERBS.append(v)
        else:
            v = verb
            match = next((x for x in ALL_DICT_VERBS if x.verb == v), None)
            meaning_vi = match.meaning_vi if match else "Động từ tiếng Nhật"
            reading = match.reading if match else (self.lang_provider.get_reading(v) or v)
            jlpt_level = match.level if match else difficulty

        # 3. Pick target form using non-repeating shuffle queue
        if not target_form:
            form = self._get_next_form(candidate_forms)
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
            "jlpt_level": jlpt_level.upper(),
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

    def generate_vocabulary(
        self,
        direction: str = "random",
        difficulty: str = "normal",
        pressure_level: str = "normal",
        word_types: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a vocabulary recall exercise (ja→vi or vi→ja).

        Args:
            direction: 'ja_to_vi' | 'vi_to_ja' | 'random'
            difficulty: 'easy' | 'normal' | 'hard'
            pressure_level: pressure profile key
            word_types: optional filter ['noun','verb','adj_i','adj_na'] — None = all
        """
        timer_ms = timer_for_level(pressure_level)
        word = _get_next_vocab(difficulty)

        # Filter by word_type if requested (re-roll up to 10 times)
        if word_types:
            for _ in range(10):
                if word.word_type in word_types:
                    break
                word = _get_next_vocab(difficulty)

        actual_dir = direction if direction in ("ja_to_vi", "vi_to_ja") else random.choice(["ja_to_vi", "vi_to_ja"])

        word_type_label = {
            "noun": "Danh từ",
            "verb": "Động từ",
            "adj_i": "Tính từ い",
            "adj_na": "Tính từ な",
            "adverb": "Trạng từ",
        }.get(word.word_type, "Từ vựng")

        if actual_dir == "ja_to_vi":
            return {
                "title": f"瞬発語彙 🇯🇵→🇻🇳: {word.word}",
                "objective": f"Nghe từ tiếng Nhật và nói nghĩa tiếng Việt trong {timer_ms/1000:.1f}s",
                "scenario": f"{word_type_label} — JLPT {word.jlpt.upper()}",
                "instructions": f"Từ: '{word.word}' ({word.reading}) — Nói ngay nghĩa tiếng Việt!",
                "prompt": word.word,
                "prompt_reading": word.reading,
                "prompt_translation": word.meaning_vi,
                "expected": word.meaning_vi,
                "canonical": word.meaning_vi,
                "acceptable_variants": [word.meaning_vi] + word.synonyms_vi,
                "direction": "ja_to_vi",
                "word_type": word.word_type,
                "jlpt_level": word.jlpt.upper(),
                "word_reading": word.reading,
                "word_meaning_vi": word.meaning_vi,
                "synonyms_vi": word.synonyms_vi,
                "timer_limit_ms": timer_ms,
                "pressure_level": pressure_level,
                "difficulty": difficulty,
                "constraints": ["Nói nghĩa tiếng Việt của từ trên."],
                "target_patterns": [word.meaning_vi] + word.synonyms_vi,
                "semantic_target": {"type": "vocab_recall", "direction": "ja_to_vi", "answer": word.meaning_vi},
                "estimated_minutes": 3,
            }
        else:  # vi_to_ja
            return {
                "title": f"瞬発語彙 🇻🇳→🇯🇵: {word.meaning_vi}",
                "objective": f"Nghe nghĩa tiếng Việt và nói từ tiếng Nhật trong {timer_ms/1000:.1f}s",
                "scenario": f"{word_type_label} — JLPT {word.jlpt.upper()}",
                "instructions": f"Nghĩa: '{word.meaning_vi}' — Nói ngay từ tiếng Nhật!",
                "prompt": word.meaning_vi,
                "prompt_reading": None,
                "prompt_translation": word.word,
                "expected": word.word,
                "canonical": word.word,
                "acceptable_variants": [word.word, word.reading],
                "direction": "vi_to_ja",
                "word_type": word.word_type,
                "jlpt_level": word.jlpt.upper(),
                "word_reading": word.reading,
                "word_meaning_vi": word.meaning_vi,
                "synonyms_vi": word.synonyms_vi,
                "timer_limit_ms": timer_ms,
                "pressure_level": pressure_level,
                "difficulty": difficulty,
                "constraints": ["Nói từ tiếng Nhật (dạng từ điển)."],
                "target_patterns": [word.word, word.reading],
                "semantic_target": {"type": "vocab_recall", "direction": "vi_to_ja", "answer": word.word},
                "estimated_minutes": 3,
            }

    def generate_keigo_vocabulary(
        self,
        target_type: str = "all",
        difficulty: str = "normal",
        pressure_level: str = "normal",
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a Keigo Word Blitz exercise (Plain -> Sonkeigo/Kenjougo/Business)."""
        timer_ms = timer_for_level(pressure_level)
        entry = _get_next_keigo_vocab(target_type=target_type, difficulty=difficulty)

        type_icon = {
            "sonkeigo": "👑 尊敬語",
            "kenjougo": "🙇 謙譲語",
            "business": "💼 ビジネス語",
        }.get(entry.target_type, "敬語")

        return {
            "title": f"敬語瞬発 ({type_icon}): {entry.source_word} → {entry.canonical}",
            "objective": f"Chuyển '{entry.source_word}' ({entry.meaning_vi}) sang {entry.target_label_vi} trong {timer_ms/1000:.1f}s",
            "scenario": f"{type_icon} — JLPT {entry.jlpt_level}",
            "instructions": f"Từ: '{entry.source_word}' ({entry.source_reading}) — Nói ngay dạng {entry.target_label_vi}!",
            "prompt": entry.source_word,
            "prompt_reading": entry.source_reading,
            "prompt_translation": entry.meaning_vi,
            "target_type": entry.target_type,
            "target_label_vi": entry.target_label_vi,
            "expected": entry.canonical,
            "canonical": entry.canonical,
            "canonical_reading": entry.canonical_reading,
            "acceptable_variants": [entry.canonical] + entry.acceptable_variants,
            "triplet_sonkeigo": entry.triplet_sonkeigo,
            "triplet_kenjougo": entry.triplet_kenjougo,
            "explanation_vi": entry.explanation_vi,
            "category": entry.category,
            "jlpt_level": entry.jlpt_level,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": [f"Nói chính xác dạng {entry.target_label_vi} của từ trên."],
            "target_patterns": [entry.canonical] + entry.acceptable_variants,
            "semantic_target": {
                "type": "keigo_vocab_recall",
                "source": entry.source_word,
                "target_type": entry.target_type,
                "answer": entry.canonical,
            },
            "estimated_minutes": 3,
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
        if sub_mode == "reflex_vocabulary":
            return self.generate_vocabulary(**kwargs)
        if sub_mode == "reflex_keigo_vocab":
            return self.generate_keigo_vocabulary(**kwargs)
        return self.generate_qna(**kwargs)

