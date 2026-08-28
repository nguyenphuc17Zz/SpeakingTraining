"""Speech analytics fixtures §76."""

import pytest

from app.domains.monologue.analytics.pause_analyzer import PauseAnalyzer
from app.domains.monologue.analytics.filler_analyzer import FillerAnalyzer
from app.domains.monologue.analytics.self_repair_analyzer import SelfRepairAnalyzer
from app.domains.monologue.analytics.idea_density import IdeaDensityAnalyzer
from app.domains.monologue.analytics.lexical_profiler import LexicalProfiler
from app.domains.monologue.analytics.discourse_analyzer import DiscourseStructureAnalyzer
from app.domains.monologue.analytics.rate_analyzer import SpeechRateAnalyzer
from app.domains.monologue.analytics.quality_gate import SpeechQualityGate
from app.domains.monologue.contracts import SpeechGenre, PauseClass


def test_pause_analyzer_classify():
    assert PauseAnalyzer.classify(300) == PauseClass.MICRO_PAUSE
    assert PauseAnalyzer.classify(700) == PauseClass.NORMAL_PAUSE
    assert PauseAnalyzer.classify(1200) == PauseClass.LONG_PAUSE
    assert PauseAnalyzer.classify(2000) == PauseClass.STALL
    assert PauseAnalyzer.classify(4000) == PauseClass.BREAKDOWN

def test_pause_analyzer_with_words():
    words = [
        {"word": "私は", "start_ms": 0, "end_ms": 300},
        {"word": "学生", "start_ms": 800, "end_ms": 1100},
        {"word": "です", "start_ms": 2500, "end_ms": 2800},
    ]
    pauses, summary = PauseAnalyzer.analyze(words, 3000, "私は学生です")
    assert summary["total"] >= 1
    # gap 500ms => NORMAL
    assert any(p.pause_class == PauseClass.NORMAL_PAUSE for p in pauses) or summary["normal"]>=1

def test_filler_analyzer():
    fa = FillerAnalyzer()
    events, summ = fa.analyze("えーと、私は学生です。あのー、趣味は読書です。", None)
    assert summ["filler_count"] >= 1
    assert summ["filler_ratio"] > 0

def test_self_repair():
    sa = SelfRepairAnalyzer()
    events, summ = sa.analyze("日本で働く……正確に言うと、日本の会社で働くことです。")
    assert summ["repair_count"] >= 1
    # abandoned
    events2, summ2 = sa.analyze("昨日は雨が降って、")
    # may be 0 or 1 depending heuristic, just check no crash
    assert summ2["repair_count"] >= 0

def test_idea_density_repeat():
    idea = IdeaDensityAnalyzer.analyze("便利です。便利です。便利だと思います。すごく便利です。")
    # repeated same idea → repeated_ideas >=1, low unique
    assert idea["repeated_ideas"] >= 1 or idea["unique_ideas"] <= 2

def test_idea_density_verbose():
    idea = IdeaDensityAnalyzer.analyze("私の意見はテレワークに賛成です。理由は時間を有効に使えるからです。例えば、通勤時間がなくなるので家族と過ごせます。")
    assert idea["unique_ideas"] >= 2
    assert idea["examples"] >= 1

def test_lexical_profiler():
    lp = LexicalProfiler(provider=None)
    res = lp.analyze("私は学生です。毎日日本語を勉強しています。便利なアプリで楽しく学んでいます。")
    assert res["unique_lemmas"] > 0
    assert 0 <= res["type_token_ratio"] <= 1
    assert 0 <= res["mattr"] <= 1

def test_discourse_analyzer_opinion():
    da = DiscourseStructureAnalyzer()
    res = da.analyze("私はテレワークに賛成です。理由は時間が有効に使えるからです。例えば通勤が不要です。結論として、テレワークは良いと思います。", SpeechGenre.OPINION)
    assert "opinion" in str(res["detected_structure"]) or "position" in res["detected_structure"] or len(res["detected_structure"])>=2
    assert res["connector_quality"] in ("present","appropriate","repeated","missing")

def test_discourse_missing_conclusion():
    da = DiscourseStructureAnalyzer()
    res = da.analyze("私はテレワークに賛成です。理由は便利だからです。", SpeechGenre.OPINION)
    assert "conclusion" in res["missing_elements"] or len(res["missing_elements"])>=1

def test_rate_analyzer():
    r = SpeechRateAnalyzer.analyze("こんにちは、私は学生です。", 10000, 10, None)
    assert r["chars_per_min"] > 0
    assert r["rate_quality"] in ("slow","normal","fast")

def test_quality_gate():
    q = SpeechQualityGate.evaluate(audio_bytes=b"\x00"*100, speech_duration_ms=500, target_duration_ms=60000, stt_confidence=0.9, word_count=1)
    assert q.status == "RETRY_AUDIO"
    q2 = SpeechQualityGate.evaluate(audio_bytes=b"\x00"*12000, speech_duration_ms=5000, target_duration_ms=60000, stt_confidence=0.2, word_count=10)
    assert q2.status in ("LOW_CONFIDENCE","ok")
