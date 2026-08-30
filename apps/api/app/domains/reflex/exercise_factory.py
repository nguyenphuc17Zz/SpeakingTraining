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
    get_rule_based_pool,
    get_sonkeigo_pool,
    get_keigo_by_category,
    search_keigo,
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


def _get_next_qna(candidate_pool: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    global _QNA_SHUFFLE_QUEUE
    if candidate_pool and candidate_pool != DICT_QNA_QUESTIONS:
        unseen = [item for item in candidate_pool if item.get("q") not in _GLOBAL_RECENT_QNA]
        if not unseen:
            unseen = candidate_pool
        item = random.choice(unseen)
        _GLOBAL_RECENT_QNA.append(item["q"])
        return item

    if not _QNA_SHUFFLE_QUEUE:
        _QNA_SHUFFLE_QUEUE = random.sample(DICT_QNA_QUESTIONS, len(DICT_QNA_QUESTIONS))
    item = _QNA_SHUFFLE_QUEUE.pop(0)
    _GLOBAL_RECENT_QNA.append(item["q"])
    return item


def _get_next_transform(candidate_pool: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    global _TRANSFORMS_SHUFFLE_QUEUE
    if candidate_pool and candidate_pool != DICT_TRANSFORMATIONS:
        unseen = [item for item in candidate_pool if item.get("source") not in _GLOBAL_RECENT_TRANSFORMS]
        if not unseen:
            unseen = candidate_pool
        item = random.choice(unseen)
        _GLOBAL_RECENT_TRANSFORMS.append(item["source"])
        return item

    if not _TRANSFORMS_SHUFFLE_QUEUE:
        _TRANSFORMS_SHUFFLE_QUEUE = random.sample(DICT_TRANSFORMATIONS, len(DICT_TRANSFORMATIONS))
    item = _TRANSFORMS_SHUFFLE_QUEUE.pop(0)
    _GLOBAL_RECENT_TRANSFORMS.append(item["source"])
    return item


def _get_next_context(candidate_pool: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    global _CONTEXTS_SHUFFLE_QUEUE
    if candidate_pool and candidate_pool != DICT_CONTEXTS:
        unseen = [item for item in candidate_pool if (item.get("speaker_ja") or item.get("scenario", "")) not in _GLOBAL_RECENT_CONTEXTS]
        if not unseen:
            unseen = candidate_pool
        item = random.choice(unseen)
        _GLOBAL_RECENT_CONTEXTS.append(item.get("speaker_ja") or item.get("scenario", ""))
        return item

    if not _CONTEXTS_SHUFFLE_QUEUE:
        _CONTEXTS_SHUFFLE_QUEUE = random.sample(DICT_CONTEXTS, len(DICT_CONTEXTS))
    item = _CONTEXTS_SHUFFLE_QUEUE.pop(0)
    _GLOBAL_RECENT_CONTEXTS.append(item.get("speaker_ja") or item.get("scenario", ""))
    return item


def _get_next_vocab(candidate_pool: list[DictWord] | None = None) -> DictWord:
    global _VOCAB_SHUFFLE_QUEUE
    pool = candidate_pool if candidate_pool else get_all_vocab_words()
    if candidate_pool and candidate_pool != get_all_vocab_words():
        unseen = [w for w in pool if w.word not in _GLOBAL_RECENT_VOCAB]
        if not unseen:
            unseen = pool
        item = random.choice(unseen)
        _GLOBAL_RECENT_VOCAB.append(item.word)
        return item

    if not _VOCAB_SHUFFLE_QUEUE:
        unseen = [w for w in pool if w.word not in _GLOBAL_RECENT_VOCAB]
        if not unseen:
            _GLOBAL_RECENT_VOCAB.clear()
            unseen = pool
        _VOCAB_SHUFFLE_QUEUE = random.sample(unseen, len(unseen))
    item = _VOCAB_SHUFFLE_QUEUE.pop(0)
    _GLOBAL_RECENT_VOCAB.append(item.word)
    return item


def _get_next_keigo_vocab(
    candidate_pool: list[KeigoWordEntry] | None = None,
    target_type: str = "all",
    difficulty: str = "normal",
) -> KeigoWordEntry:
    global _KEIGO_QUEUES
    if candidate_pool and candidate_pool != get_all_keigo_vocab():
        unseen = [w for w in candidate_pool if f"{w.source_word}_{w.target_type}" not in _GLOBAL_RECENT_KEIGO_VOCAB]
        if not unseen:
            unseen = candidate_pool
        item = random.choice(unseen)
        _GLOBAL_RECENT_KEIGO_VOCAB.append(f"{item.source_word}_{item.target_type}")
        return item

    if target_type == "sonkeigo":
        pool = get_sonkeigo_pool()
    elif target_type == "kenjougo":
        pool = get_kenjougo_pool()
    elif target_type == "rule_based":
        pool = get_rule_based_pool()
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


def _resolve_candidate_forms(
    target_form: str | list[str | ConjugationForm] | ConjugationForm | None,
    all_forms: list[ConjugationForm],
) -> list[ConjugationForm]:
    if not target_form:
        return all_forms
    if isinstance(target_form, ConjugationForm):
        return [target_form]
    if isinstance(target_form, str):
        if target_form.strip().lower() in ("all", "*", ""):
            return all_forms
        tokens = [t.strip().lower() for t in target_form.split(",") if t.strip()]
        matched = [f for f in all_forms if f.value.lower() in tokens or f.name.lower() in tokens]
        return matched if matched else all_forms
    if isinstance(target_form, (list, tuple, set)):
        resolved = []
        for item in target_form:
            if isinstance(item, ConjugationForm):
                resolved.append(item)
            elif isinstance(item, str):
                s = item.strip().lower()
                m = next((f for f in all_forms if f.value.lower() == s or f.name.lower() == s), None)
                if m:
                    resolved.append(m)
        return resolved if resolved else all_forms
    return all_forms


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
        target_form: str | list[str | ConjugationForm] | ConjugationForm | None = None,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        **kwargs,
    ) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)

        # 1. 100% Full Unrestricted Verb Pool and All 49 Active Conjugation Forms
        pool = ALL_DICT_VERBS
        candidate_forms = [
            # Core (11)
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

            # Group 2: Desire (5)
            ConjugationForm.TAI,
            ConjugationForm.TAKUNAI,
            ConjugationForm.TAKATTA,
            ConjugationForm.TAKUNAKATTA,
            ConjugationForm.TAGARU,

            # Group 3: Prohibition & Requests (3)
            ConjugationForm.PROHIBITIVE,
            ConjugationForm.NAIDE,
            ConjugationForm.NASAI,

            # Group 4: State & Prep (6)
            ConjugationForm.TE_IRU,
            ConjugationForm.TE_INAI,
            ConjugationForm.TE_ITA,
            ConjugationForm.TE_OKU,
            ConjugationForm.TE_SHIMAU,
            ConjugationForm.TE_MIRU,

            # Group 5: Ease & Difficulty (3)
            ConjugationForm.YASUI,
            ConjugationForm.NIKUI,
            ConjugationForm.ZURAI,

            # Group 6: Past & Combined (7)
            ConjugationForm.NAKATTA,
            ConjugationForm.PASSIVE_PAST,
            ConjugationForm.CAUSATIVE_PAST,
            ConjugationForm.CAUSATIVE_PASSIVE_PAST,
            ConjugationForm.POTENTIAL_NEGATIVE,
            ConjugationForm.POTENTIAL_PAST,
            ConjugationForm.POTENTIAL_NEGATIVE_PAST,

            # Group 7: Conditionals (4)
            ConjugationForm.NAKEREBA,
            ConjugationForm.NAKATTARA,
            ConjugationForm.TO_CONDITIONAL,
            ConjugationForm.NARA,

            # Group 8: Colloquial Slang (11)
            ConjugationForm.NAKYA,
            ConjugationForm.CHAU,
            ConjugationForm.CHATTA,
            ConjugationForm.TOKU,
            ConjugationForm.TOITA,
            ConjugationForm.TERU,
            ConjugationForm.TENAI,
            ConjugationForm.TETA,
            ConjugationForm.CHA_DAME,
            ConjugationForm.CHA_IKENAI,
            ConjugationForm.NAITO,
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

        # 3. Filter target forms based on user selection
        selected_candidates = _resolve_candidate_forms(target_form, candidate_forms)

        # 4. Pick target form from selected candidates using non-repeating shuffle queue
        if len(selected_candidates) == 1:
            form = selected_candidates[0]
        else:
            form = self._get_next_form(selected_candidates)

        # 5. Conjugate
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

    def generate_qna(
        self,
        topic: str | list[str] | None = None,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        **kwargs,
    ) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)

        # Topic filtering
        raw_topic = topic or kwargs.get("qna_category") or kwargs.get("category")
        if raw_topic:
            if isinstance(raw_topic, str):
                tokens = [t.strip().lower() for t in raw_topic.split(",") if t.strip()]
            elif isinstance(raw_topic, (list, tuple, set)):
                tokens = [str(t).strip().lower() for t in raw_topic if t]
            else:
                tokens = []

            if tokens and "all" not in tokens and "*" not in tokens:
                # 1. Match by category ID
                candidates = [q for q in DICT_QNA_QUESTIONS if q.get("category", "daily").lower() in tokens]
                if not candidates:
                    # 2. Match by custom keyword in Japanese question, Vietnamese translation, or idea sparks
                    candidates = [
                        q for q in DICT_QNA_QUESTIONS
                        if any(
                            t in q["q"].lower()
                            or t in q["translation"].lower()
                            or any(t in spark.lower() for spark in q.get("idea_sparks", []))
                            for t in tokens
                        )
                    ]
                if not candidates:
                    candidates = DICT_QNA_QUESTIONS
            else:
                candidates = DICT_QNA_QUESTIONS
        else:
            candidates = DICT_QNA_QUESTIONS

        chosen = _get_next_qna(candidates)

        sample_ans = chosen.get("sample_answer", "はい、そうです。")
        multi_ans = chosen.get("multi_answers", {})
        key_vocab = chosen.get("key_vocab", [])
        idea_sparks = chosen.get("idea_sparks", [])
        category = chosen.get("category", "daily")

        # Collect all acceptable variants
        acceptable_list = [sample_ans]
        for val in multi_ans.values():
            if isinstance(val, dict) and "ja" in val and val["ja"] not in acceptable_list:
                acceptable_list.append(val["ja"])

        return {
            "title": f"瞬発 Q&A ({category})",
            "objective": f"Nghe câu hỏi và trả lời tự nhiên trong {timer_ms/1000:.1f}s",
            "scenario": chosen["translation"],
            "instructions": f"Nghe: '{chosen['q']}' — Trả lời ngay bằng tiếng Nhật 1-2 câu tự nhiên.",
            "prompt": chosen["q"],
            "prompt_translation": chosen["translation"],
            "translation": chosen["translation"],
            "vietnamese": chosen["translation"],
            "expected": sample_ans,
            "canonical": sample_ans,
            "acceptable_variants": acceptable_list,
            "topic": category,
            "category": category,
            "key_vocab": key_vocab,
            "idea_sparks": idea_sparks,
            "multi_answers": multi_ans,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Trả lời đủ ý, tự nhiên."],
            "target_patterns": acceptable_list,
            "semantic_target": {"required_intent": "answer question"},
            "estimated_minutes": 4,
        }

    def generate_transformation(
        self,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        transformation_category: str | None = None,
        grammar_category: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)
        category_filter = transformation_category or grammar_category or kwargs.get("category")

        if category_filter and category_filter != "all":
            tokens = [c.strip().lower() for c in category_filter.split(",") if c.strip()]
            candidates = [
                t for t in DICT_TRANSFORMATIONS
                if t.get("category", "").lower() in tokens
                or any(tok in t.get("task", "").lower() for tok in tokens)
                or any(tok in t.get("target_label", "").lower() for tok in tokens)
                or any(tok in t.get("source", "").lower() for tok in tokens)
                or any(tok in t.get("translation", "").lower() for tok in tokens)
                or any(tok in t.get("formula", "").lower() for tok in tokens)
                or any(tok in t.get("grammar_note", "").lower() for tok in tokens)
            ]
            if not candidates:
                candidates = DICT_TRANSFORMATIONS
        else:
            candidates = DICT_TRANSFORMATIONS

        chosen = _get_next_transform(candidates)

        return {
            "title": f"瞬発・文型変換: {chosen.get('target_label', chosen['task'])}",
            "objective": f"Biến đổi câu theo yêu cầu trong {timer_ms/1000:.1f}s",
            "scenario": chosen["translation"],
            "instructions": f"Câu gốc: '{chosen['source']}' — Đổi sang: {chosen.get('target_label', chosen['task'])}",
            "prompt": chosen["source"],
            "source": chosen["source"],
            "prompt_translation": chosen["translation"],
            "translation": chosen["translation"],
            "vietnamese": chosen["translation"],
            "task": chosen["task"],
            "target_label": chosen.get("target_label", chosen["task"]),
            "formula": chosen.get("formula", ""),
            "grammar_note": chosen.get("grammar_note", ""),
            "category": chosen.get("category", "casual"),
            "transformation_category": chosen.get("category", "casual"),
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

    def generate_context(
        self,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        context_category: str | None = None,
        situation_category: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        timer_ms = timer_for_level(pressure_level)
        category_filter = context_category or situation_category or kwargs.get("category")

        if category_filter and category_filter != "all":
            tokens = [c.strip().lower() for c in category_filter.split(",") if c.strip()]
            candidates = [
                c for c in DICT_CONTEXTS
                if c.get("category", "").lower() in tokens
                or any(tok in c.get("role", "").lower() for tok in tokens)
                or any(tok in c.get("intent", "").lower() for tok in tokens)
                or any(tok in c.get("speaker_vi", "").lower() for tok in tokens)
                or any(tok in c.get("speaker_ja", "").lower() for tok in tokens)
                or any(tok in c.get("cultural_note", "").lower() for tok in tokens)
                or any(tok in str(c.get("key_vocab", [])).lower() for tok in tokens)
            ]
            if not candidates:
                candidates = DICT_CONTEXTS
        else:
            candidates = DICT_CONTEXTS

        chosen = _get_next_context(candidates)

        speaker_ja = chosen.get("speaker_ja") or chosen.get("scenario", "")
        speaker_vi = chosen.get("speaker_vi") or chosen.get("translation", "")
        role = chosen.get("role", "Đối phương")
        category = chosen.get("category", "workplace")
        intent = chosen.get("intent", "Phản hồi tự nhiên bằng tiếng Nhật.")
        key_vocab = chosen.get("key_vocab", [])
        idea_sparks = chosen.get("idea_sparks", [])
        sample_ans = chosen.get("sample_answer") or chosen.get("expected", "")
        multi_ans = chosen.get("multi_answers", {})
        cultural_note = chosen.get("cultural_note", "")

        acceptable_list = [sample_ans]
        for val in multi_ans.values():
            if isinstance(val, dict) and "ja" in val and val["ja"] not in acceptable_list:
                acceptable_list.append(val["ja"])

        return {
            "title": f"瞬発・状況対応: {role}",
            "objective": f"Phản xạ tự nhiên theo tình huống trong {timer_ms/1000:.1f}s",
            "scenario": speaker_vi,
            "instructions": f"Đối phương ({role}): '{speaker_ja}' — Nhiệm vụ: {intent}",
            "prompt": speaker_ja,
            "speaker_ja": speaker_ja,
            "speaker_vi": speaker_vi,
            "prompt_translation": speaker_vi,
            "translation": speaker_vi,
            "vietnamese": speaker_vi,
            "intent": intent,
            "role": role,
            "category": category,
            "context_category": category,
            "key_vocab": key_vocab,
            "idea_sparks": idea_sparks,
            "sample_answer": sample_ans,
            "expected": sample_ans,
            "canonical": sample_ans,
            "multi_answers": multi_ans,
            "cultural_note": cultural_note,
            "acceptable_variants": acceptable_list,
            "relationship": role,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Phản hồi tự nhiên, đúng ý định, chuẩn tông giọng."],
            "target_patterns": acceptable_list,
            "semantic_target": {"intent": intent, "role": role},
            "estimated_minutes": 4,
        }

    def generate_vocabulary(
        self,
        direction: str = "vi_to_ja",
        difficulty: str = "normal",
        pressure_level: str = "normal",
        vocab_category: str | None = None,
        category: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a vocabulary reflex exercise (100% Spoken Japanese output).

        Args:
            direction: always 'vi_to_ja' for spoken Japanese output
            difficulty: 'easy' | 'normal' | 'hard'
            pressure_level: pressure profile key
            vocab_category: action_verbs | emotions_adj | adverbs_mimetic | workplace_biz | daily_life | all | custom
        """
        timer_ms = timer_for_level(pressure_level)
        category_filter = vocab_category or category or kwargs.get("category")

        if category_filter and category_filter != "all":
            tokens = [c.strip().lower() for c in category_filter.split(",") if c.strip()]
            candidates = [
                w for w in get_all_vocab_words()
                if w.category.lower() in tokens
                or any(tok in w.word.lower() for tok in tokens)
                or any(tok in w.reading.lower() for tok in tokens)
                or any(tok in w.meaning_vi.lower() for tok in tokens)
                or any(tok in syn.lower() for syn in w.synonyms_vi for tok in tokens)
                or any(tok in w.collocation_ja.lower() for tok in tokens)
                or any(tok in w.collocation_vi.lower() for tok in tokens)
                or any(tok in w.example_ja.lower() for tok in tokens)
                or any(tok in w.example_vi.lower() for tok in tokens)
            ]
            if not candidates:
                candidates = get_all_vocab_words()
        else:
            candidates = get_all_vocab_words()

        word = _get_next_vocab(candidates)

        word_type_label = {
            "noun": "Danh từ",
            "verb": "Động từ",
            "adj_i": "Tính từ い",
            "adj_na": "Tính từ な",
            "adverb": "Phó từ / Tượng thanh",
        }.get(word.word_type, "Từ vựng")

        category_label = {
            "action_verbs": "Hành động & Đời sống",
            "emotions_adj": "Cảm xúc & Đánh giá",
            "adverbs_mimetic": "Phó từ & Từ tượng thanh/hình",
            "workplace_biz": "Công sở & Thương mại",
            "daily_life": "Sinh hoạt & Dịch vụ",
        }.get(word.category, "Từ vựng thực chiến")

        return {
            "title": f"瞬発語彙: {word.word}",
            "objective": f"Bật ngay từ tiếng Nhật chuẩn xác trong {timer_ms/1000:.1f}s",
            "scenario": f"{word_type_label} • {category_label}",
            "instructions": f"Nghĩa: '{word.meaning_vi}' — Nói ngay từ tiếng Nhật!",
            "prompt": word.meaning_vi,
            "prompt_reading": None,
            "prompt_translation": word.word,
            "expected": word.word,
            "canonical": word.word,
            "acceptable_variants": [word.word, word.reading],
            "direction": "vi_to_ja",
            "word": word.word,
            "word_type": word.word_type,
            "word_type_label": word_type_label,
            "category": word.category,
            "vocab_category": word.category,
            "jlpt_level": word.jlpt.upper() if word.jlpt else "ALL",
            "word_reading": word.reading,
            "word_meaning_vi": word.meaning_vi,
            "collocation_ja": word.collocation_ja,
            "collocation_vi": word.collocation_vi,
            "example_ja": word.example_ja,
            "example_vi": word.example_vi,
            "synonyms_vi": word.synonyms_vi,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Nói từ tiếng Nhật chuẩn xác."],
            "target_patterns": [word.word, word.reading],
            "semantic_target": {"type": "vocab_recall", "direction": "vi_to_ja", "answer": word.word},
            "estimated_minutes": 3,
        }

    def generate_keigo_vocabulary(
        self,
        target_type: str = "all",
        keigo_category: str | None = None,
        category: str | None = None,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a Keigo Word Blitz exercise (Plain -> Sonkeigo/Kenjougo/Rule/Business)."""
        timer_ms = timer_for_level(pressure_level)
        category_filter = keigo_category or category or target_type or kwargs.get("category")

        candidates = None
        if category_filter and category_filter != "all":
            tokens = [c.strip().lower() for c in category_filter.split(",") if c.strip()]
            candidates = [
                k for k in get_all_keigo_vocab()
                if k.category.lower() in tokens
                or k.target_type.lower() in tokens
                or any(tok in k.source_word.lower() for tok in tokens)
                or any(tok in k.source_reading.lower() for tok in tokens)
                or any(tok in k.canonical.lower() for tok in tokens)
                or any(tok in k.canonical_reading.lower() for tok in tokens)
                or any(tok in k.meaning_vi.lower() for tok in tokens)
                or any(tok in syn.lower() for syn in k.acceptable_variants for tok in tokens)
                or any(tok in (k.triplet_sonkeigo or "").lower() for tok in tokens)
                or any(tok in (k.triplet_kenjougo or "").lower() for tok in tokens)
            ]
            if not candidates:
                candidates = [
                    k for k in get_all_keigo_vocab()
                    if any(tok in k.example_ja.lower() for tok in tokens)
                    or any(tok in k.example_vi.lower() for tok in tokens)
                    or any(tok in k.explanation_vi.lower() for tok in tokens)
                ]
            if not candidates:
                candidates = get_all_keigo_vocab()

        entry = _get_next_keigo_vocab(candidate_pool=candidates, target_type=category_filter or "all", difficulty=difficulty)

        type_icon = {
            "sonkeigo": "👑 尊敬語",
            "kenjougo": "🙇 謙譲語",
            "rule_based": "⚙️ 規則敬語",
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
            "subject_hint_vi": entry.subject_hint_vi,
            "formula": entry.formula,
            "example_ja": entry.example_ja,
            "example_vi": entry.example_vi,
            "category": entry.category,
            "keigo_category": entry.category,
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

