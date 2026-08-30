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
    """Verify that consecutive conjugation calls cycle through all 49 distinct forms and verbs."""
    from app.domains.reflex.exercise_factory import _CONJ_FORMS_SHUFFLE_QUEUE
    _CONJ_FORMS_SHUFFLE_QUEUE.clear()
    f = ReflexExerciseFactory()
    forms = [f.generate_conjugation(difficulty="normal")["form"] for _ in range(49)]
    verbs = [f.generate_conjugation(difficulty="normal")["prompt"] for _ in range(49)]

    # In 49 consecutive calls of a full cycle, we must cover all 49 distinct forms
    assert len(set(forms)) == 49, f"Expected 49 distinct forms in 49 calls, got {len(set(forms))} ({set(forms)})"
    assert len(set(verbs)) >= 45, f"Expected high verb variety, got {len(set(verbs))}"


@pytest.mark.asyncio
async def test_dynamic_generator_conjugation_rotation():
    """Verify AIReflexGenerator routes reflex_conjugation through the full 49-form rotation queue."""
    from app.domains.reflex.dynamic_generator import AIReflexGenerator
    from app.domains.reflex.exercise_factory import _CONJ_FORMS_SHUFFLE_QUEUE
    _CONJ_FORMS_SHUFFLE_QUEUE.clear()
    gen = AIReflexGenerator(None)
    forms = []
    for _ in range(49):
        ex = await gen.generate_dynamic_exercise(sub_mode="reflex_conjugation", difficulty="easy", pressure_level="relaxed")
        forms.append(ex["form"])

    # All 49 forms must cycle without restriction
    assert len(set(forms)) == 49, f"Expected all 49 forms across dynamic generator calls, got {len(set(forms))}"


def test_conjugation_engine_comprehensive():
    """Verify deterministic conjugation for Godan, Ichidan, Suru, Kuru, and Iku."""
    from app.domains.reflex.conjugation_engine import JapaneseConjugationEngine, ConjugationForm

    engine = JapaneseConjugationEngine()

    # 1. Godan: 書く
    assert engine.conjugate("書く", ConjugationForm.NAI).canonical == "書かない"
    assert engine.conjugate("書く", ConjugationForm.NAKATTA).canonical == "書かなかった"
    assert engine.conjugate("書く", ConjugationForm.TAI).canonical == "書きたい"
    assert engine.conjugate("書く", ConjugationForm.TAKUNAI).canonical == "書きたくない"
    assert engine.conjugate("書く", ConjugationForm.TAKATTA).canonical == "書きたかった"
    assert engine.conjugate("書く", ConjugationForm.TAKUNAKATTA).canonical == "書きたくなかった"
    assert engine.conjugate("書く", ConjugationForm.PROHIBITIVE).canonical == "書くな"
    assert engine.conjugate("書く", ConjugationForm.NAIDE).canonical == "書かないで"
    assert engine.conjugate("書く", ConjugationForm.NASAI).canonical == "書きなさい"
    assert engine.conjugate("書く", ConjugationForm.YASUI).canonical == "書きやすい"
    assert engine.conjugate("書く", ConjugationForm.NIKUI).canonical == "書きにくい"
    assert engine.conjugate("書く", ConjugationForm.ZURAI).canonical == "書きづらい"
    assert engine.conjugate("書く", ConjugationForm.TE_IRU).canonical == "書いている"
    assert engine.conjugate("書く", ConjugationForm.CHAU).canonical == "書いちゃう"
    assert engine.conjugate("書く", ConjugationForm.TOKU).canonical == "書いとく"
    assert engine.conjugate("書く", ConjugationForm.TERU).canonical == "書いてる"
    assert engine.conjugate("書く", ConjugationForm.CHA_DAME).canonical == "書いちゃだめ"
    assert engine.conjugate("書く", ConjugationForm.NAKYA).canonical == "書かなきゃ"
    assert engine.conjugate("書く", ConjugationForm.POTENTIAL_NEGATIVE).canonical == "書けない"
    assert engine.conjugate("書く", ConjugationForm.POTENTIAL_PAST).canonical == "書けた"
    assert engine.conjugate("書く", ConjugationForm.POTENTIAL_NEGATIVE_PAST).canonical == "書けなかった"
    assert engine.conjugate("書く", ConjugationForm.PASSIVE_PAST).canonical == "書かれた"
    assert engine.conjugate("書く", ConjugationForm.CAUSATIVE_PAST).canonical == "書かせた"
    assert engine.conjugate("書く", ConjugationForm.CAUSATIVE_PASSIVE_PAST).canonical == "書かせられた"

    # 2. Godan (de-sound): 飲む
    assert engine.conjugate("飲む", ConjugationForm.TE).canonical == "飲んで"
    assert engine.conjugate("飲む", ConjugationForm.CHAU).canonical == "飲んじゃう"
    assert engine.conjugate("飲む", ConjugationForm.TOKU).canonical == "飲んどく"
    assert engine.conjugate("飲む", ConjugationForm.TERU).canonical == "飲んでる"
    assert engine.conjugate("飲む", ConjugationForm.CHA_DAME).canonical == "飲んじゃだめ"

    # 3. Ichidan: 食べる
    assert engine.conjugate("食べる", ConjugationForm.NAI).canonical == "食べない"
    assert engine.conjugate("食べる", ConjugationForm.NAKATTA).canonical == "食べなかった"
    assert engine.conjugate("食べる", ConjugationForm.TAI).canonical == "食べたい"
    assert engine.conjugate("食べる", ConjugationForm.TAKATTA).canonical == "食べたかった"
    assert engine.conjugate("食べる", ConjugationForm.PROHIBITIVE).canonical == "食べるな"
    assert engine.conjugate("食べる", ConjugationForm.NASAI).canonical == "食べなさい"
    assert engine.conjugate("食べる", ConjugationForm.CHAU).canonical == "食べちゃう"
    assert engine.conjugate("食べる", ConjugationForm.TOKU).canonical == "食べとく"
    assert engine.conjugate("食べる", ConjugationForm.TERU).canonical == "食べてる"
    assert engine.conjugate("食べる", ConjugationForm.POTENTIAL).canonical == "食べられる"
    assert "食べれる" in engine.conjugate("食べる", ConjugationForm.POTENTIAL).accepted
    assert engine.conjugate("食べる", ConjugationForm.POTENTIAL_NEGATIVE).canonical == "食べられない"
    assert "食べれない" in engine.conjugate("食べる", ConjugationForm.POTENTIAL_NEGATIVE).accepted

    # 4. Irregular: する
    assert engine.conjugate("する", ConjugationForm.NAI).canonical == "しない"
    assert engine.conjugate("する", ConjugationForm.NAKATTA).canonical == "しなかった"
    assert engine.conjugate("する", ConjugationForm.TAI).canonical == "したい"
    assert engine.conjugate("する", ConjugationForm.POTENTIAL).canonical == "できる"
    assert engine.conjugate("する", ConjugationForm.POTENTIAL_NEGATIVE).canonical == "できない"
    assert engine.conjugate("する", ConjugationForm.POTENTIAL_PAST).canonical == "できた"
    assert engine.conjugate("する", ConjugationForm.PASSIVE).canonical == "される"
    assert engine.conjugate("する", ConjugationForm.CAUSATIVE).canonical == "させる"
    assert engine.conjugate("する", ConjugationForm.CHAU).canonical == "しちゃう"
    assert engine.conjugate("する", ConjugationForm.TOKU).canonical == "しとく"
    assert engine.conjugate("する", ConjugationForm.NAKYA).canonical == "しなきゃ"

    # 5. Irregular: 来る
    assert engine.conjugate("来る", ConjugationForm.NAI).canonical == "来ない"
    assert engine.conjugate("来る", ConjugationForm.NAKATTA).canonical == "来なかった"
    assert engine.conjugate("来る", ConjugationForm.TAI).canonical == "来たい"
    assert engine.conjugate("来る", ConjugationForm.POTENTIAL).canonical == "来られる"
    assert engine.conjugate("来る", ConjugationForm.PASSIVE).canonical == "来られる"
    assert engine.conjugate("来る", ConjugationForm.CAUSATIVE).canonical == "来させる"
    assert engine.conjugate("来る", ConjugationForm.CHAU).canonical == "来ちゃう"
    assert engine.conjugate("来る", ConjugationForm.TOKU).canonical == "来とく"
    assert engine.conjugate("くる", ConjugationForm.NAI).canonical == "こない"
    assert engine.conjugate("くる", ConjugationForm.TA).canonical == "きた"
    assert engine.conjugate("くる", ConjugationForm.CHAU).canonical == "きちゃう"

    # 6. Special exception: 行く
    assert engine.conjugate("行く", ConjugationForm.TE).canonical == "行って"
    assert engine.conjugate("行く", ConjugationForm.TA).canonical == "行った"
    assert engine.conjugate("行く", ConjugationForm.CHAU).canonical == "行っちゃう"
    assert engine.conjugate("行く", ConjugationForm.TOKU).canonical == "行っとく"


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


def test_reflex_conjugation_target_form_filter():
    """Verify that specifying target_form filters generation to only the requested form(s)."""
    from app.domains.reflex.conjugation_engine import ConjugationForm
    factory = ReflexExerciseFactory()

    # 1. Single form as string
    for _ in range(10):
        ex = factory.generate_conjugation(target_form="chatta")
        assert ex["form"] == "chatta"

    # 2. Comma-separated list of forms
    allowed = {"passive", "causative", "causative_passive"}
    for _ in range(20):
        ex = factory.generate_conjugation(target_form="passive,causative,causative_passive")
        assert ex["form"] in allowed

    # 3. List of ConjugationForm enums
    allowed_enums = [ConjugationForm.TAI, ConjugationForm.TAKUNAI]
    for _ in range(10):
        ex = factory.generate_conjugation(target_form=allowed_enums)
        assert ex["form"] in {"tai", "takunai"}

    # 4. 'all' form option allows all forms
    ex_all = factory.generate_conjugation(target_form="all")
    assert ex_all["form"] is not None



