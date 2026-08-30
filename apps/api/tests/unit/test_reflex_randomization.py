import pytest
from app.domains.reflex.exercise_factory import ReflexExerciseFactory, _GLOBAL_RECENT_QNA, _QNA_SHUFFLE_QUEUE
from app.domains.reflex.dictionary_pool import DICT_QNA_QUESTIONS


def test_reflex_qna_randomization_no_repeats():
    """Verify that calling generate_qna 50 times produces 50 unique questions with 0% repeats."""
    factory = ReflexExerciseFactory()
    seen = []
    for _ in range(50):
        # Even if a new factory is instantiated each time (simulating HTTP requests)
        f = ReflexExerciseFactory()
        ex = f.generate_qna(difficulty="normal", pressure_level="normal")
        prompt = ex["prompt"]
        seen.append(prompt)

    # 50 consecutive calls from a 100+ pool must all be distinct
    unique_count = len(set(seen))
    assert unique_count == 50, f"Expected 50 unique prompts, but got {unique_count}. Repeats: {[p for p in seen if seen.count(p) > 1]}"


def test_reflex_conjugation_form_rotation_variety():
    """Verify that consecutive conjugation calls cycle through distinct forms and verbs."""
    from app.domains.reflex.exercise_factory import _CONJ_FORMS_SHUFFLE_QUEUE
    _CONJ_FORMS_SHUFFLE_QUEUE.clear()
    f = ReflexExerciseFactory()
    forms = [f.generate_conjugation(difficulty="normal")["form"] for _ in range(11)]
    verbs = [f.generate_conjugation(difficulty="normal")["prompt"] for _ in range(11)]

    # In 11 consecutive calls of a full cycle, we must cover all 11 distinct forms and 11 unique verbs
    assert len(set(forms)) == 11, f"Expected 11 distinct forms in 11 calls, got {len(set(forms))} ({set(forms)})"
    assert len(set(verbs)) == 11, f"Expected 11 unique verbs, got {len(set(verbs))}"


@pytest.mark.asyncio
async def test_dynamic_generator_conjugation_rotation():
    """Verify AIReflexGenerator routes reflex_conjugation through the rotation queue."""
    from app.domains.reflex.dynamic_generator import AIReflexGenerator
    from app.domains.reflex.exercise_factory import _CONJ_FORMS_SHUFFLE_QUEUE
    _CONJ_FORMS_SHUFFLE_QUEUE.clear()
    gen = AIReflexGenerator(None)
    forms = []
    for _ in range(11):
        ex = await gen.generate_dynamic_exercise(sub_mode="reflex_conjugation", difficulty="easy", pressure_level="relaxed")
        forms.append(ex["form"])

    # Even when difficulty is easy and pressure is relaxed, all 11 forms must cycle without restriction
    assert len(set(forms)) == 11, f"Expected all 11 forms across dynamic generator calls, got {set(forms)}"


def test_reflex_transformation_and_context_variety():
    """Verify variety in transformation and context generators."""
    f = ReflexExerciseFactory()
    transforms = [f.generate_transformation()["prompt"] for _ in range(25)]
    contexts = [f.generate_context()["prompt"] for _ in range(14)]

    assert len(set(transforms)) == 25
    assert len(set(contexts)) == 14


def test_reflex_vocabulary_generation():
    """Verify vocabulary generation across directions and difficulty."""
    f = ReflexExerciseFactory()
    seen = []
    for _ in range(40):
        ex = f.generate_vocabulary(difficulty="normal")
        assert "title" in ex
        assert "prompt" in ex
        assert "direction" in ex
        assert ex["direction"] in ("ja_to_vi", "vi_to_ja")
        assert "word_type" in ex
        assert "jlpt_level" in ex
        seen.append(ex["prompt"])

    assert len(set(seen)) >= 35, f"Expected high variety in 40 vocab calls, got {len(set(seen))}"


@pytest.mark.asyncio
async def test_reflex_vocabulary_evaluation():
    """Verify deterministic vocabulary evaluator for both directions."""
    from app.domains.reflex.reflex_evaluator import ReflexEvaluator
    evaluator = ReflexEvaluator(None)  # db is None, no db/AI needed for vocabulary

    # 1. JA -> VI correct
    res = await evaluator.evaluate_vocabulary(
        word="食べる",
        direction="ja_to_vi",
        word_reading="たべる",
        word_meaning_vi="ăn",
        synonyms_vi=["ăn uống"],
        user_transcript="ăn",
        timer_limit_ms=3000,
        reaction_latency_ms=800,
    )
    assert res["success"] is True
    assert res["score"] >= 80

    # 2. JA -> VI synonym match
    res_syn = await evaluator.evaluate_vocabulary(
        word="食べる",
        direction="ja_to_vi",
        word_reading="たべる",
        word_meaning_vi="ăn",
        synonyms_vi=["ăn uống"],
        user_transcript="ăn uống",
        timer_limit_ms=3000,
        reaction_latency_ms=900,
    )
    assert res_syn["success"] is True

    # 3. VI -> JA correct
    res_ja = await evaluator.evaluate_vocabulary(
        word="学校",
        direction="vi_to_ja",
        word_reading="がっこう",
        word_meaning_vi="trường học",
        synonyms_vi=[],
        user_transcript="がっこう",
        timer_limit_ms=3000,
        reaction_latency_ms=1000,
    )
    assert res_ja["success"] is True
    assert res_ja["score"] >= 80

    # 4. VI -> JA incorrect
    res_fail = await evaluator.evaluate_vocabulary(
        word="学校",
        direction="vi_to_ja",
        word_reading="がっこう",
        word_meaning_vi="trường học",
        synonyms_vi=[],
        user_transcript="たべる",
        timer_limit_ms=3000,
        reaction_latency_ms=1000,
    )
    assert res_fail["success"] is False


def test_reflex_keigo_vocabulary_generation():
    """Verify Keigo vocabulary blitz generation and filter pools."""
    f = ReflexExerciseFactory()

    # Test sonkeigo filter
    sonkei_ex = f.generate_keigo_vocabulary(target_type="sonkeigo")
    assert sonkei_ex["target_type"] == "sonkeigo"
    assert "👑 尊敬語" in sonkei_ex["title"]
    assert sonkei_ex["canonical"]

    # Test kenjougo filter
    kenjou_ex = f.generate_keigo_vocabulary(target_type="kenjougo")
    assert kenjou_ex["target_type"] == "kenjougo"
    assert "🙇 謙譲語" in kenjou_ex["title"]

    # Test business filter
    biz_ex = f.generate_keigo_vocabulary(target_type="business")
    assert biz_ex["target_type"] == "business"
    assert "💼 ビジネス語" in biz_ex["title"]

    # Test high variety across 30 calls
    seen = [f.generate_keigo_vocabulary(target_type="all")["prompt"] for _ in range(30)]
    assert len(set(seen)) >= 20


@pytest.mark.asyncio
async def test_reflex_keigo_vocabulary_evaluation():
    """Verify deterministic evaluation of Keigo vocabulary blitz."""
    from app.domains.reflex.reflex_evaluator import ReflexEvaluator
    evaluator = ReflexEvaluator(None)

    # 1. Exact canonical match: 食べる -> 召し上がる
    res1 = await evaluator.evaluate_keigo_vocabulary(
        source_word="食べる",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="召し上がる",
        acceptable_variants=["召し上がる", "召し上がります", "めしあがる"],
        user_transcript="召し上がる",
        timer_limit_ms=3000,
        reaction_latency_ms=900,
    )
    assert res1["success"] is True
    assert res1["score"] >= 85

    # 2. Polite form variant: 食べる -> 召し上がります
    res2 = await evaluator.evaluate_keigo_vocabulary(
        source_word="食べる",
        target_type="sonkeigo",
        target_label_vi="Tôn kính ngữ (尊敬語)",
        canonical="召し上がる",
        acceptable_variants=["召し上がる", "召し上がります", "めしあがる"],
        user_transcript="召し上がります",
        timer_limit_ms=3000,
        reaction_latency_ms=950,
    )
    assert res2["success"] is True

    # 3. Kenjougo match: 見る -> 拝見する
    res3 = await evaluator.evaluate_keigo_vocabulary(
        source_word="見る",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="拝見する",
        acceptable_variants=["拝見する", "拝見します", "はいけんする"],
        user_transcript="拝見します",
        timer_limit_ms=3000,
        reaction_latency_ms=750,
    )
    assert res3["success"] is True

    # 4. Incorrect answer
    res4 = await evaluator.evaluate_keigo_vocabulary(
        source_word="見る",
        target_type="kenjougo",
        target_label_vi="Khiêm nhường ngữ (謙譲語)",
        canonical="拝見する",
        acceptable_variants=["拝見する", "拝見します"],
        user_transcript="みます",
        timer_limit_ms=3000,
        reaction_latency_ms=1000,
    )
    assert res4["success"] is False


